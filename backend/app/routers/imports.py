import csv
from io import StringIO
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Milestone, Project

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/projects")
def import_projects(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = _decode_file(file)

    reader = _build_reader(raw)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Leere CSV oder fehlende Kopfzeile")

    stats = {"projects_created": 0, "projects_updated": 0, "milestones_created": 0, "milestones_updated": 0}

    current_project = None

    for row in reader:
        project_raw = _raw(row, ["project_name", "Projekte"])
        project_name = project_raw.strip() if project_raw else ""
        project = None

        if project_name:
            kunde = _pick(row, ["kunde", "Kunde", "Kunden"]) or None
            notizen = _pick(row, ["notizen", "Notizen"]) or None
            project = db.query(Project).filter(Project.name == project_name).one_or_none()
            if not project:
                project = Project(name=project_name, kunde=kunde, notizen=notizen)
                db.add(project)
                stats["projects_created"] += 1
            else:
                updated = False
                if kunde and kunde != project.kunde:
                    project.kunde = kunde
                    updated = True
                if notizen and notizen != project.notizen:
                    project.notizen = notizen
                    updated = True
                if updated:
                    stats["projects_updated"] += 1
            db.flush()
            current_project = project
        elif current_project:
            project = current_project
        else:
            continue

        milestone_name = _pick(row, ["milestone_name", "Arbeitspaket", "Milestone", "Meilenstein"])
        if milestone_name:
            milestone = (
                db.query(Milestone)
                .filter(Milestone.project_id == project.id, Milestone.name == milestone_name)
                .one_or_none()
            )
            if not milestone:
                milestone = Milestone(
                    project_id=project.id,
                    name=milestone_name,
                    soll_stunden=_parse_number(_pick(row, ["soll_stunden", "Sollstunden"])),
                    ist_stunden=_parse_number(_pick(row, ["ist_stunden", "Erbrachte Stunden"])),
                    bonus_relevant=_parse_bool(_pick(row, ["bonus_relevant", "Bonus"])),
                )
                db.add(milestone)
                stats["milestones_created"] += 1
            else:
                soll_stunden = _parse_number(_pick(row, ["soll_stunden", "Sollstunden"]))
                if soll_stunden is not None:
                    milestone.soll_stunden = soll_stunden
                ist_stunden = _parse_number(_pick(row, ["ist_stunden", "Erbrachte Stunden"]))
                if ist_stunden is not None:
                    milestone.ist_stunden = ist_stunden
                bonus_relevant = _parse_bool(_pick(row, ["bonus_relevant", "Bonus"]))
                if bonus_relevant is not None:
                    milestone.bonus_relevant = bonus_relevant
                stats["milestones_updated"] += 1

    db.commit()
    return stats


def _build_reader(raw: str) -> csv.DictReader:
    buffer = StringIO(raw)
    sample = buffer.read(4096)
    buffer.seek(0)
    delimiter = "\t"
    try:
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
    except csv.Error:
        if ";" in sample:
            delimiter = ";"
        elif "," in sample:
            delimiter = ","
    return csv.DictReader(buffer, delimiter=delimiter)


def _decode_file(upload: UploadFile) -> str:
    data = upload.file.read()
    encodings = ["utf-8-sig", "utf-16", "utf-16le", "utf-16be", "latin-1"]
    for enc in encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="Datei kann nicht dekodiert werden (versucht utf-8/utf-16/latin-1)")


def _pick(row: Dict[str, str], keys):
    for key in keys:
        if key in row and row[key] is not None:
            value = str(row[key]).strip()
            if value:
                return value
    return None


def _raw(row: Dict[str, str], keys):
    for key in keys:
        if key in row and row[key] is not None:
            return str(row[key])
    return None


def _parse_number(value):
    if value in (None, "", "None"):
        return None
    value = str(value).strip()
    value = value.replace(".", "").replace(" ", "").replace("\xa0", "")
    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def _parse_bool(value):
    if value is None:
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "ja"}
