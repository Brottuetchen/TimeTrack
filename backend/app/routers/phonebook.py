import csv
from io import StringIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from .. import schemas
from ..database import get_db
from ..models import PhoneBook

router = APIRouter(prefix="/phonebook", tags=["phonebook"])


@router.get("", response_model=List[schemas.PhoneBookRead])
def list_phonebook(
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search in name, number, company"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Liste aller PhoneBook-Einträge mit optionaler Suche."""
    query = db.query(PhoneBook)

    if user_id:
        query = query.filter(PhoneBook.user_id == user_id)

    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            (PhoneBook.name.ilike(search_pattern))
            | (PhoneBook.number.ilike(search_pattern))
            | (PhoneBook.company.ilike(search_pattern))
        )

    entries = query.order_by(PhoneBook.name).offset(offset).limit(limit).all()
    return entries


@router.get("/{entry_id}", response_model=schemas.PhoneBookRead)
def get_phonebook_entry(entry_id: int, db: Session = Depends(get_db)):
    """Einzelner PhoneBook-Eintrag."""
    entry = db.get(PhoneBook, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="PhoneBook entry not found")
    return entry


@router.post("", response_model=schemas.PhoneBookRead, status_code=201)
def create_phonebook_entry(payload: schemas.PhoneBookCreate, db: Session = Depends(get_db)):
    """Erstellt einen neuen PhoneBook-Eintrag."""
    # Konvertiere tags zu JSON-kompatiblem Format
    tags_json = payload.tags if payload.tags else []

    entry = PhoneBook(
        name=payload.name,
        number=payload.number,
        company=payload.company,
        tags=tags_json,
        user_id=payload.user_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{entry_id}", response_model=schemas.PhoneBookRead)
def update_phonebook_entry(
    entry_id: int, payload: schemas.PhoneBookUpdate, db: Session = Depends(get_db)
):
    """Aktualisiert einen PhoneBook-Eintrag."""
    entry = db.get(PhoneBook, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="PhoneBook entry not found")

    # Update nur gesetzte Felder
    if payload.name is not None:
        entry.name = payload.name
    if payload.number is not None:
        entry.number = payload.number
    if payload.company is not None:
        entry.company = payload.company
    if payload.tags is not None:
        entry.tags = payload.tags

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_phonebook_entry(entry_id: int, db: Session = Depends(get_db)):
    """Löscht einen PhoneBook-Eintrag."""
    entry = db.get(PhoneBook, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="PhoneBook entry not found")
    db.delete(entry)
    db.commit()
    return None


@router.get("/lookup/{number}", response_model=Optional[schemas.PhoneBookRead])
def lookup_number(number: str, user_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Sucht einen Namen für eine Telefonnummer.
    Normalisiert die Nummer (entfernt Leerzeichen, +, etc.) für besseres Matching.
    """
    # Normalisiere Nummer
    normalized_search = number.replace(" ", "").replace("+", "").replace("-", "")

    query = db.query(PhoneBook)

    if user_id:
        query = query.filter(PhoneBook.user_id == user_id)

    # Suche nach exakter oder Teilübereinstimmung
    entry = query.filter(
        PhoneBook.number.contains(normalized_search)
        | PhoneBook.number.like(f"%{normalized_search}")
    ).first()

    return entry


@router.post("/import/csv")
async def import_phonebook_csv(
    file: UploadFile = File(...),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    CSV-Import für PhoneBook.
    Format: name,number,company,tags
    Tags als komma-separierte Werte in Quotes: "tag1,tag2"
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Datei muss .csv sein")

    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))

    created_count = 0
    updated_count = 0

    for row in reader:
        name = row.get("name", "").strip()
        number = row.get("number", "").strip()
        company = row.get("company", "").strip()
        tags_str = row.get("tags", "").strip()

        if not name or not number:
            continue  # Skip ungültige Zeilen

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []

        # Prüfe ob Eintrag existiert (gleiche Nummer + user_id)
        existing = db.query(PhoneBook).filter(
            PhoneBook.number == number,
            PhoneBook.user_id == user_id
        ).first()

        if existing:
            # Update
            existing.name = name
            existing.company = company or None
            existing.tags = tags
            updated_count += 1
        else:
            # Create
            entry = PhoneBook(
                name=name,
                number=number,
                company=company or None,
                tags=tags,
                user_id=user_id,
            )
            db.add(entry)
            created_count += 1

    db.commit()

    return {
        "created_count": created_count,
        "updated_count": updated_count,
        "total": created_count + updated_count,
    }


@router.get("/export/csv")
def export_phonebook_csv(user_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Export aller PhoneBook-Einträge als CSV.
    Format: name,number,company,tags
    """
    query = db.query(PhoneBook)

    if user_id:
        query = query.filter(PhoneBook.user_id == user_id)

    entries = query.order_by(PhoneBook.name).all()

    rows = []
    for entry in entries:
        tags_str = ",".join(entry.tags) if entry.tags else ""
        rows.append({
            "name": entry.name,
            "number": entry.number,
            "company": entry.company or "",
            "tags": tags_str,
        })

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["name", "number", "company", "tags"])
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)

    filename = f"phonebook_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
