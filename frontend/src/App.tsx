import React, { useState, useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import { apiClient, Event, CreateEventData } from "./lib/api";
import { useCountdown } from "./hooks/useCountdown";
import { useTheme } from "./hooks/useTheme";
import "./index.css";

// Color bucket helper
const getColorClasses = (colorBucket: string | null) => {
  switch (colorBucket) {
    case "RED":
      return "bg-red-500/20 border-red-500";
    case "ORANGE":
      return "bg-orange-500/20 border-orange-500";
    case "YELLOW":
      return "bg-yellow-500/20 border-yellow-500";
    case "GREEN":
      return "bg-green-500/20 border-green-500";
    case "CYAN":
      return "bg-cyan-500/20 border-cyan-500";
    case "BLUE":
      return "bg-blue-500/20 border-blue-500";
    case "PURPLE":
      return "bg-purple-500/20 border-purple-500";
    default:
      return "bg-gray-500/20 border-gray-500";
  }
};

// Event Card Component
function EventCard({
  event,
  serverNow,
  onClick,
}: {
  event: Event;
  serverNow: string;
  onClick: () => void;
}) {
  const countdown = useCountdown(event.effective_due_at, serverNow);
  const colorClasses = getColorClasses(event.color_bucket);

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg border-2 cursor-pointer hover:shadow-lg transition ${colorClasses}`}
    >
      <h3 className="font-bold text-lg mb-2">{event.title}</h3>
      {event.description && (
        <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
          {event.description}
        </p>
      )}
      <div className="flex items-center justify-between">
        <span className="text-2xl font-mono font-bold">
          {countdown.formatted}
        </span>
        <span className="text-xs px-2 py-1 bg-black/10 dark:bg-white/10 rounded">
          {event.color_bucket || "OVERDUE"}
        </span>
      </div>
      {event.repeat_interval !== "none" && (
        <div className="mt-2 text-xs text-muted-foreground">
          🔄 Repeats {event.repeat_interval}
        </div>
      )}
    </div>
  );
}

// Main App
function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/finished" element={<FinishedPage />} />
      <Route path="/share/:token" element={<SharePage />} />
    </Routes>
  );
}

// Home Page
function HomePage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [serverNow, setServerNow] = useState<string>(new Date().toISOString());
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    loadUser();
    loadEvents();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Not authenticated");
    }
  };

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listEvents({ q: searchQuery });
      setEvents(data.items);
      setServerNow(data.server_now);
    } catch (error) {
      console.error("Failed to load events:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = () => {
    window.location.href = "/api/auth/google/login";
  };

  const handleLogout = async () => {
    await apiClient.logout();
    setUser(null);
    window.location.reload();
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  const handleCreateEvent = async (data: CreateEventData) => {
    try {
      console.log("Creating event with data:", data);
      await apiClient.createEvent(data);
      setShowCreateModal(false);
      loadEvents();
    } catch (error) {
      console.error("Failed to create event:", error);
      alert("Failed to create event");
    }
  };

  const handleDeleteEvent = async (id: string) => {
    if (!confirm("Delete this event?")) return;
    try {
      await apiClient.deleteEvent(id);
      loadEvents();
    } catch (error) {
      console.error("Failed to delete event:", error);
    }
  };

  const handleShare = async (eventId: string) => {
    try {
      const result = await apiClient.createShareToken(eventId);
      navigator.clipboard.writeText(result.share_url);
      alert("Share link copied to clipboard!");
    } catch (error) {
      console.error("Failed to create share link:", error);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">⏱️ Countdowns</h1>
          <div className="flex items-center gap-4">
            <input
              type="text"
              placeholder="Search events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadEvents()}
              className="px-3 py-2 border rounded-lg bg-background"
            />
            <button
              onClick={toggleTheme}
              className="px-3 py-2 border rounded-lg hover:bg-accent"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
            {user ? (
              <div className="flex items-center gap-2">
                <span className="text-sm">{user.name}</span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 border rounded-lg hover:bg-accent text-sm"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={handleLogin}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90"
              >
                Sign in with Google
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b">
        <div className="container mx-auto px-4 flex gap-4">
          <Link
            to="/"
            className="px-4 py-2 border-b-2 border-primary font-medium"
          >
            Upcoming
          </Link>
          <Link
            to="/finished"
            className="px-4 py-2 border-b-2 border-transparent hover:border-primary/50"
          >
            Finished
          </Link>
        </div>
      </div>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        {!user ? (
          <div className="text-center py-12">
            <p className="text-xl mb-4">
              Sign in to create and manage your countdowns
            </p>
            <button
              onClick={handleLogin}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg text-lg"
            >
              Sign in with Google
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-xl font-bold">Your Events</h2>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90"
              >
                + New Event
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12">Loading...</div>
            ) : events.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No events yet. Create your first countdown!
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {events.map((event) => (
                  <div key={event.id} className="relative group">
                    <EventCard
                      event={event}
                      serverNow={serverNow}
                      onClick={() => {}}
                    />
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition flex gap-2">
                      <button
                        onClick={() => handleShare(event.id)}
                        className="px-2 py-1 bg-blue-500 text-white rounded text-xs"
                      >
                        Share
                      </button>
                      <button
                        onClick={() => handleDeleteEvent(event.id)}
                        className="px-2 py-1 bg-red-500 text-white rounded text-xs"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateEventModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateEvent}
        />
      )}
    </div>
  );
}

// Create Event Modal
function CreateEventModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (data: CreateEventData) => void;
}) {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    event_date: "",
    repeat_interval: "none" as "none" | "day" | "week" | "month" | "year",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate({
      title: formData.title,
      description: formData.description || null,
      event_date: new Date(formData.event_date).toISOString(),
      repeat_interval: formData.repeat_interval,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Create New Event</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Title *</label>
              <input
                type="text"
                required
                maxLength={120}
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Description
              </label>
              <textarea
                maxLength={2000}
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg bg-background"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Date & Time *
              </label>
              <input
                type="datetime-local"
                required
                value={formData.event_date}
                onChange={(e) =>
                  setFormData({ ...formData, event_date: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Repeat</label>
              <select
                value={formData.repeat_interval}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    repeat_interval: e.target.value as any,
                  })
                }
                className="w-full px-3 py-2 border rounded-lg bg-background"
              >
                <option value="none">None</option>
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
                <option value="month">Monthly</option>
                <option value="year">Yearly</option>
              </select>
            </div>
          </div>
          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Finished Page
function FinishedPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const data = await apiClient.listEvents({ include_overdue: true });
      const overdue = data.items.filter((e) => e.is_overdue);
      setEvents(overdue);
    } catch (error) {
      console.error("Failed to load events:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <Link to="/" className="text-2xl font-bold">
            ⏱️ Countdowns
          </Link>
        </div>
      </header>
      <div className="container mx-auto px-4 py-8">
        <h2 className="text-xl font-bold mb-6">Finished Events</h2>
        {loading ? (
          <div>Loading...</div>
        ) : events.length === 0 ? (
          <div className="text-muted-foreground">No finished events</div>
        ) : (
          <div className="space-y-4">
            {events.map((event) => (
              <div key={event.id} className="p-4 border rounded-lg bg-muted/50">
                <h3 className="font-bold">{event.title}</h3>
                <p className="text-sm text-muted-foreground">Completed</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Share Page
function SharePage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      apiClient
        .getSharePreview(token)
        .then(setPreview)
        .catch(() => alert("Share link not found"))
        .finally(() => setLoading(false));
    }
  }, [token]);

  const handleImport = async () => {
    if (!token) return;
    try {
      await apiClient.importSharedEvent(token);
      alert("Event imported successfully!");
      navigate("/");
    } catch (error: any) {
      if (error.message.includes("401")) {
        window.location.href = "/api/auth/google/login";
      } else {
        alert("Failed to import event");
      }
    }
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="max-w-md w-full p-6 border rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Shared Event</h2>
        {preview && (
          <>
            <h3 className="text-xl font-semibold mb-2">{preview.title}</h3>
            {preview.description && (
              <p className="text-muted-foreground mb-4">
                {preview.description}
              </p>
            )}
            <p className="text-sm mb-4">
              Date: {new Date(preview.event_date).toLocaleString()}
            </p>
            <button
              onClick={handleImport}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg"
            >
              Add to My Events
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
