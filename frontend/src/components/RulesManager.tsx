import { useState, useEffect } from "react";
import clsx from "clsx";
import { AssignmentRule, Project, Milestone } from "../types";
import { fetchRules, fetchProjects, fetchMilestones, createRule, updateRule, deleteRule } from "../api";

interface Props {
  userId: string;
}

export function RulesManager({ userId }: Props) {
  const [rules, setRules] = useState<AssignmentRule[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingRule, setEditingRule] = useState<AssignmentRule | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    process_pattern: "",
    title_contains: "",
    auto_project_id: "",
    auto_milestone_id: "",
    auto_activity: "",
    auto_comment_template: "",
    priority: "0",
  });

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    try {
      const [rulesData, projectsData, milestonesData] = await Promise.all([
        fetchRules({ user_id: userId }),
        fetchProjects(),
        fetchMilestones(),
      ]);
      setRules(rulesData);
      setProjects(projectsData);
      setMilestones(milestonesData);
    } catch (error) {
      console.error("Error loading rules:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      user_id: userId,
      name: formData.name,
      process_pattern: formData.process_pattern || undefined,
      title_contains: formData.title_contains || undefined,
      auto_project_id: formData.auto_project_id ? parseInt(formData.auto_project_id) : undefined,
      auto_milestone_id: formData.auto_milestone_id ? parseInt(formData.auto_milestone_id) : undefined,
      auto_activity: formData.auto_activity || undefined,
      auto_comment_template: formData.auto_comment_template || undefined,
      priority: parseInt(formData.priority),
    };

    try {
      if (editingRule) {
        await updateRule(editingRule.id, payload);
      } else {
        await createRule(payload);
      }
      resetForm();
      loadData();
    } catch (error) {
      console.error("Error saving rule:", error);
      alert("Fehler beim Speichern der Regel");
    }
  };

  const handleEdit = (rule: AssignmentRule) => {
    setEditingRule(rule);
    setFormData({
      name: rule.name,
      process_pattern: rule.process_pattern || "",
      title_contains: rule.title_contains || "",
      auto_project_id: rule.auto_project_id?.toString() || "",
      auto_milestone_id: rule.auto_milestone_id?.toString() || "",
      auto_activity: rule.auto_activity || "",
      auto_comment_template: rule.auto_comment_template || "",
      priority: rule.priority.toString(),
    });
    setShowForm(true);
  };

  const handleDelete = async (ruleId: number) => {
    if (!confirm("Regel wirklich löschen?")) return;

    try {
      await deleteRule(ruleId);
      loadData();
    } catch (error) {
      console.error("Error deleting rule:", error);
      alert("Fehler beim Löschen");
    }
  };

  const handleToggleEnabled = async (rule: AssignmentRule) => {
    try {
      await updateRule(rule.id, { enabled: !rule.enabled });
      loadData();
    } catch (error) {
      console.error("Error toggling rule:", error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      process_pattern: "",
      title_contains: "",
      auto_project_id: "",
      auto_milestone_id: "",
      auto_activity: "",
      auto_comment_template: "",
      priority: "0",
    });
    setEditingRule(null);
    setShowForm(false);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between bg-white dark:bg-slate-800 p-4 rounded-md border border-slate-200 dark:border-slate-700">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
            ⚡ Auto-Assignment Regeln ({rules.length})
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Definiere Regeln für automatische Projekt-Zuweisung (100% lokal)
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-md"
        >
          {showForm ? "Abbrechen" : "+ Neue Regel"}
        </button>
      </div>

      {/* Info-Box */}
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-3 text-sm">
        <strong>ℹ️ Matching-Engine:</strong> Alle Regeln laufen lokal (Regex/String-Matching). Keine KI, keine Cloud.
      </div>

      {/* Regel-Formular */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-4 space-y-4">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">
            {editingRule ? "Regel bearbeiten" : "Neue Regel erstellen"}
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Regel-Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="z.B. AutoCAD Projekt-X"
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Priorität
              </label>
              <input
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              />
              <p className="text-xs text-slate-500 mt-1">Höhere Zahl = höhere Priorität</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Prozess-Pattern
              </label>
              <input
                type="text"
                value={formData.process_pattern}
                onChange={(e) => setFormData({ ...formData, process_pattern: e.target.value })}
                placeholder="z.B. acad.exe oder *.exe"
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              />
              <p className="text-xs text-slate-500 mt-1">Wildcard: * = beliebig viele Zeichen</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Titel enthält
              </label>
              <input
                type="text"
                value={formData.title_contains}
                onChange={(e) => setFormData({ ...formData, title_contains: e.target.value })}
                placeholder="z.B. Projekt-X"
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              />
              <p className="text-xs text-slate-500 mt-1">Case-insensitive</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Auto-Projekt
              </label>
              <select
                value={formData.auto_project_id}
                onChange={(e) => setFormData({ ...formData, auto_project_id: e.target.value })}
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              >
                <option value="">-- Kein Projekt --</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Auto-Milestone
              </label>
              <select
                value={formData.auto_milestone_id}
                onChange={(e) => setFormData({ ...formData, auto_milestone_id: e.target.value })}
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              >
                <option value="">-- Kein Milestone --</option>
                {milestones
                  .filter((m) => !formData.auto_project_id || m.project_id === parseInt(formData.auto_project_id))
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Activity
              </label>
              <input
                type="text"
                value={formData.auto_activity}
                onChange={(e) => setFormData({ ...formData, auto_activity: e.target.value })}
                placeholder="z.B. Entwicklung"
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Kommentar-Template
              </label>
              <input
                type="text"
                value={formData.auto_comment_template}
                onChange={(e) => setFormData({ ...formData, auto_comment_template: e.target.value })}
                placeholder="z.B. Arbeit an {title}"
                className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-800 dark:text-slate-100"
              />
              <p className="text-xs text-slate-500 mt-1">Variablen: {"{title}"}, {"{process}"}</p>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md"
            >
              {editingRule ? "Aktualisieren" : "Erstellen"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="px-4 py-2 bg-slate-300 hover:bg-slate-400 text-slate-800 rounded-md"
            >
              Abbrechen
            </button>
          </div>
        </form>
      )}

      {/* Regeln-Liste */}
      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 dark:bg-slate-700 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-200">
            <tr>
              <th className="px-2 py-3">Aktiv</th>
              <th className="px-2 py-3">Name</th>
              <th className="px-2 py-3">Bedingungen</th>
              <th className="px-2 py-3">Auto-Projekt</th>
              <th className="px-2 py-3">Priorität</th>
              <th className="px-2 py-3">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 && (
              <tr>
                <td colSpan={6} className="px-2 py-8 text-center text-slate-500 dark:text-slate-400">
                  Noch keine Regeln definiert. Erstelle deine erste Regel für automatische Zuweisung.
                </td>
              </tr>
            )}
            {rules.map((rule) => (
              <tr
                key={rule.id}
                className={clsx(
                  "border-b border-slate-200 dark:border-slate-700 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-700",
                  !rule.enabled && "opacity-50"
                )}
              >
                <td className="px-2 py-3 align-top">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={() => handleToggleEnabled(rule)}
                    className="w-4 h-4"
                  />
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100 font-medium">
                  {rule.name}
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100 text-xs">
                  {rule.process_pattern && (
                    <div>
                      <span className="text-slate-500">Prozess:</span> {rule.process_pattern}
                    </div>
                  )}
                  {rule.title_contains && (
                    <div>
                      <span className="text-slate-500">Titel:</span> "{rule.title_contains}"
                    </div>
                  )}
                  {!rule.process_pattern && !rule.title_contains && (
                    <span className="text-slate-400">Keine Bedingungen</span>
                  )}
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100">
                  {rule.project?.name || <span className="text-slate-400">-</span>}
                  {rule.milestone && (
                    <div className="text-xs text-slate-500">→ {rule.milestone.name}</div>
                  )}
                </td>
                <td className="px-2 py-3 align-top text-center text-slate-800 dark:text-slate-100">
                  <span className="inline-block px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs">
                    {rule.priority}
                  </span>
                </td>
                <td className="px-2 py-3 align-top">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(rule)}
                      className="text-blue-500 hover:text-blue-600 text-xs"
                    >
                      Bearbeiten
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-red-500 hover:text-red-600 text-xs"
                    >
                      Löschen
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
