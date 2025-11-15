import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { fetchProjects, fetchMilestones } from "../api";
import { Project, Milestone } from "../types";

export function MasterdataManagement() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"projects" | "milestones">("projects");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [projectsData, milestonesData] = await Promise.all([
        fetchProjects(),
        fetchMilestones(),
      ]);
      setProjects(projectsData);
      setMilestones(milestonesData);
    } catch (err) {
      console.error(err);
      toast.error("Fehler beim Laden der Stammdaten");
    } finally {
      setLoading(false);
    }
  };

  const exportProjects = () => {
    const url = `${import.meta.env.VITE_API_BASE || window.location.protocol + "//" + window.location.hostname + ":8000"}/export/projects/csv`;
    window.open(url, "_blank");
    toast.success("CSV-Export gestartet");
  };

  const exportMilestones = () => {
    const url = `${import.meta.env.VITE_API_BASE || window.location.protocol + "//" + window.location.hostname + ":8000"}/export/milestones/csv`;
    window.open(url, "_blank");
    toast.success("CSV-Export gestartet");
  };

  if (loading) {
    return <div className="p-6 text-center text-slate-500 dark:text-slate-400">Lädt...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
          Stammdaten-Management
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Verwalte Projekte und Milestones. Exportiere Daten als CSV.
        </p>
      </div>

      {/* Tab-Navigation */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab("projects")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === "projects"
              ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
          }`}
        >
          Projekte ({projects.length})
        </button>
        <button
          onClick={() => setActiveTab("milestones")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === "milestones"
              ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
          }`}
        >
          Milestones ({milestones.length})
        </button>
      </div>

      {/* Projects Tab */}
      {activeTab === "projects" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-semibold text-slate-900 dark:text-white">Projekte</h4>
            <button
              onClick={exportProjects}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
            >
              CSV exportieren
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              Keine Projekte vorhanden
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
                    <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Projekt
                    </th>
                    <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Kunde
                    </th>
                    <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Notizen
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((project) => (
                    <tr
                      key={project.id}
                      className="border-b border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    >
                      <td className="p-3 text-sm text-slate-900 dark:text-slate-100">
                        {project.name}
                      </td>
                      <td className="p-3 text-sm text-slate-600 dark:text-slate-400">
                        {project.kunde || "–"}
                      </td>
                      <td className="p-3 text-sm text-slate-600 dark:text-slate-400">
                        {project.notizen || "–"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Milestones Tab */}
      {activeTab === "milestones" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-semibold text-slate-900 dark:text-white">Milestones</h4>
            <button
              onClick={exportMilestones}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
            >
              CSV exportieren
            </button>
          </div>

          {milestones.length === 0 ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              Keine Milestones vorhanden
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
                    <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Projekt
                    </th>
                    <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Milestone
                    </th>
                    <th className="text-right p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Soll (h)
                    </th>
                    <th className="text-right p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Ist (h)
                    </th>
                    <th className="text-center p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Bonus
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {milestones.map((milestone) => {
                    const project = projects.find((p) => p.id === milestone.project_id);
                    return (
                      <tr
                        key={milestone.id}
                        className="border-b border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      >
                        <td className="p-3 text-sm text-slate-600 dark:text-slate-400">
                          {project?.name || "–"}
                        </td>
                        <td className="p-3 text-sm text-slate-900 dark:text-slate-100">
                          {milestone.name}
                        </td>
                        <td className="p-3 text-sm text-right text-slate-600 dark:text-slate-400">
                          {milestone.soll_stunden?.toFixed(1) || "–"}
                        </td>
                        <td className="p-3 text-sm text-right text-slate-600 dark:text-slate-400">
                          {milestone.ist_stunden?.toFixed(1) || "–"}
                        </td>
                        <td className="p-3 text-sm text-center">
                          {milestone.bonus_relevant ? (
                            <span className="text-green-600 dark:text-green-400">✓</span>
                          ) : (
                            <span className="text-slate-300 dark:text-slate-600">–</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Info Box */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-900 dark:text-blue-200">
          <strong>Hinweis:</strong> Zum Erstellen, Bearbeiten oder Löschen von Projekten/Milestones nutze
          bitte den Daten-Import-Tab oder füge die entsprechende UI hier hinzu.
        </p>
      </div>
    </div>
  );
}
