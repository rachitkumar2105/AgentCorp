import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../integration/hooks/use-auth';


type Version = 'V1' | 'V2';
type Screen = 'login' | 'loading' | 'shell';
type ShellView = 'home' | 'chat' | 'projects' | 'goals' | 'tasks' | 'agents' | 'workflows' | 'knowledge' | 'memory' | 'observability' | 'settings' | 'about';
type ThemeMode = 'dark' | 'light';
type WorkspaceState = 'empty' | 'loading' | 'error';
type CommandTarget = Exclude<ShellView, 'agents' | 'workflows' | 'knowledge' | 'memory' | 'observability'> | 'agents-placeholder' | 'knowledge-placeholder' | 'memory-placeholder';
type PlatformSection = 'observability' | 'architecture' | 'timeline';
type SettingsSection = 'general' | 'appearance' | 'notifications' | 'runtime' | 'ai' | 'security' | 'profile' | 'workspace' | 'version' | 'organizations' | 'integrations';

const storageKey = 'agentcorp.frontend';
const defaultVersion: Version = 'V2';
const defaultTheme: ThemeMode = 'dark';

function readStoredState() {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return {};
    return JSON.parse(raw) as Partial<{ version: Version; theme: ThemeMode }>;
  } catch {
    return {};
  }
}

const stored = typeof window !== 'undefined' ? readStoredState() : {};

export function App() {
  const [screen, setScreen] = useState<Screen>('login');
  const [version, setVersion] = useState<Version>(stored.version ?? defaultVersion);
  const [theme, setTheme] = useState<ThemeMode>(stored.theme ?? defaultTheme);
  const [shellView, setShellView] = useState<ShellView>('home');
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [clock, setClock] = useState(new Date());
  const [runtimeClock, setRuntimeClock] = useState(new Date());
  const [projectsDrawerOpen, setProjectsDrawerOpen] = useState(false);
  const [projectsLayout, setProjectsLayout] = useState<'grid' | 'list'>('grid');
  const [projectsSort, setProjectsSort] = useState('Updated');
  const [projectsFilter, setProjectsFilter] = useState('All Projects');
  const [projectsSearch, setProjectsSearch] = useState('');
  const [selectedProjectName, setSelectedProjectName] = useState<string | null>(null);
  const [goalsState] = useState<WorkspaceState>('empty');
  const [tasksState] = useState<WorkspaceState>('empty');
  const [chatState] = useState<WorkspaceState>('empty');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState('');
  const [selectedAiNode, setSelectedAiNode] = useState<string | null>(null);
  const [platformSection, setPlatformSection] = useState<PlatformSection>('observability');
  const [settingsSection, setSettingsSection] = useState<SettingsSection>('general');
  const [docSection, setDocSection] = useState('overview');

  useEffect(() => {
    const interval = window.setInterval(() => {
      setClock(new Date());
      setRuntimeClock((current) => (screen === 'loading' ? current : new Date()));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [screen]);

  const { authenticated, login, logout, loading: authLoading, user } = useAuth();

  useEffect(() => {
    if (authLoading) {
      setScreen('loading');
    } else if (authenticated) {
      setScreen('shell');
    } else {
      setScreen('login');
    }
  }, [authenticated, authLoading]);

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify({ version, theme }));
    document.documentElement.dataset.theme = theme;
  }, [version, theme]);

  useEffect(() => {
    document.documentElement.dataset.version = version;
  }, [version]);

  const isConnected = navigator.onLine;

  const versionCopy = useMemo(() => {
    return version === 'V1'
      ? 'Traditional enterprise workspace'
      : 'AI operating system with runtime, governance, and observability';
  }, [version]);

  const visibleViews = useMemo<ShellView[]>(() => {
    const base: ShellView[] = ['home', 'projects', 'goals', 'tasks', 'settings', 'about'];
    if (version === 'V2') {
      return ['home', 'chat', 'projects', 'goals', 'tasks', 'agents', 'workflows', 'knowledge', 'memory', 'observability', 'settings', 'about'];
    }
    return base;
  }, [version]);

  useEffect(() => {
    if (!visibleViews.includes(shellView)) {
      setShellView('home');
    }
  }, [shellView, visibleViews]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCommandPaletteOpen(true);
      }
      if (event.key === 'Escape') {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    if (shellView !== 'projects') {
      setProjectsDrawerOpen(false);
      setSelectedProjectName(null);
    }
  }, [shellView]);

  if (screen === 'loading') {
    return (
      <main className="loading-screen" aria-live="polite">
        <div className="loading-card">
          <div className="loading-brand">AgentCorp</div>
          <p className="loading-motto">Enterprise AI Operating System</p>
          <div className="progress-track" aria-hidden="true">
            <div className="progress-bar" />
          </div>
        </div>
      </main>
    );
  }

  if (screen === 'login') {
    return (
      <main className="auth-screen">
        <section className="auth-card minimal-card">
          <div className="brand-lockup">
            <div className="brand-mark" aria-hidden="true">AC</div>
            <div>
              <h1>AgentCorp</h1>
              <p>Enterprise AI Operating System</p>
            </div>
          </div>

          <form
            className="auth-form"
            onSubmit={async (event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              const email = formData.get('email') as string;
              const password = formData.get('password') as string;
              try {
                await login({ email, password });
              } catch (err: any) {
                alert(err.message || 'Login failed');
              }
            }}
          >
            <label>
              Email
              <input type="email" name="email" required placeholder="name@company.com" />
            </label>
            <label>
              Password
              <input type="password" name="password" required placeholder="Password" />
            </label>
            <label className="remember-row">
              <input type="checkbox" />
              Remember Me
            </label>

            <div className="auth-links">
              <button type="button" className="link-button">Forgot Password</button>
            </div>

            <button type="submit" className="primary full-width">Sign In</button>


            <div className="provider-row" aria-label="Social sign in options">
              <button type="button" className="ghost">Google</button>
              <button type="button" className="ghost">GitHub</button>
              <button type="button" className="ghost">Microsoft</button>
            </div>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand-row">
            <div className="brand-mark">AC</div>
            <div>
              <strong>AgentCorp</strong>
              <span>{version}</span>
            </div>
          </div>

          <nav className="nav">
            {visibleViews.map((item) => (
              <NavButton
                key={item}
                active={shellView === item}
                onClick={() => setShellView(item)}
              >
                {labelForView(item)}
              </NavButton>
            ))}
          </nav>
        </div>

        <div className="sidebar-footer">
          <button className="ghost" onClick={logout}>Sign Out</button>
        </div>
      </aside>

      <section className="workspace">
        <header className="header">
          <div className="header-copy">
            <p className="eyebrow">Enterprise workspace</p>
            <h2>{version === 'V1' ? 'Traditional Workspace' : 'AI Operating System'}</h2>
          </div>

          <div className="header-tools">
            <input className="search" placeholder="Search" aria-label="Search" />
            <button className="ghost">Notifications</button>
            <button className="ghost">Profile</button>
            <button type="button" className="ghost" aria-label="Open command palette" onClick={() => setCommandPaletteOpen(true)}>Ctrl + K</button>
            <VersionSwitch value={version} onChange={setVersion} />
            <ThemeSwitch value={theme} onChange={setTheme} />
          </div>
        </header>

        <section className="content">
          <div className="page-grid">
            <div className="page-main">
              {shellView === 'home' && <HomeView version={version} />}
              {shellView === 'chat' && version === 'V2' && <ChatView version={version} state={chatState} />}
              {shellView === 'goals' && <GoalsView state={goalsState} />}
              {shellView === 'tasks' && <TasksView state={tasksState} />}
              {shellView === 'agents' && version === 'V2' && <AgentsView state="empty" />}
              {shellView === 'workflows' && version === 'V2' && <WorkflowBuilderView state="empty" selectedNode={selectedAiNode} onSelectNode={setSelectedAiNode} />}
              {shellView === 'knowledge' && version === 'V2' && <KnowledgeView state="empty" />}
              {shellView === 'memory' && version === 'V2' && <MemoryView state="empty" />}
              {shellView === 'observability' && version === 'V2' && (
                <EnterprisePlatformView section={platformSection} onSectionChange={setPlatformSection} />
              )}
              {shellView === 'settings' && <SettingsView version={version} section={settingsSection} onSectionChange={setSettingsSection} />}
              {shellView === 'about' && <AboutView section={docSection} onSectionChange={setDocSection} />}
            </div>

            {shellView !== 'about' && (
              <aside className={inspectorOpen ? 'inspector open' : 'inspector closed'}>
                <div className="inspector-header">
                  <strong>{version === 'V2' && isAiWorkspace(shellView) ? 'Runtime Inspector' : 'Inspector'}</strong>
                  <button type="button" className="link-button" onClick={() => setInspectorOpen((current) => !current)}>
                    {inspectorOpen ? 'Collapse' : 'Expand'}
                  </button>
                </div>
                {inspectorOpen && (
                  isAiWorkspace(shellView) && version === 'V2' ? (
                    <div className="inspector-content runtime-inspector">
                      <InspectorRow label="Runtime Version" value={version} />
                      <InspectorRow label="Execution Context" value="AI Workspace" />
                      <InspectorRow label="Current Project" value={selectedProjectName ?? 'No project selected'} />
                      <InspectorRow label="Goal" value="No goal selected" />
                      <InspectorRow label="Task" value="No task selected" />
                      <InspectorRow label="Selected Agent" value="No agent selected" />
                      <InspectorRow label="Current Workflow" value={shellView === 'workflows' ? 'Workflow Builder' : 'No workflow selected'} />
                      <InspectorRow label="Knowledge Context" value={shellView === 'knowledge' ? 'Knowledge Base' : 'No knowledge context'} />
                      <InspectorRow label="Memory Context" value={shellView === 'memory' ? 'Memory Explorer' : 'No memory context'} />
                      <InspectorRow label="Connected Tools" value={shellView === 'observability' ? 'Tool Registry' : 'No tools selected'} />
                      <InspectorRow label="Execution Status" value={isConnected ? 'Connected' : 'Disconnected'} />
                    </div>
                  ) : (
                    <div className="inspector-content">
                      <InspectorRow label="Runtime Version" value={version} />
                      <InspectorRow label="Workspace" value={shellView === 'projects' ? 'Projects' : shellView} />
                      <InspectorRow label="Selected Project" value={selectedProjectName ?? 'No project selected'} />
                      <InspectorRow label="Selected Page" value={shellView === 'projects' ? 'Projects Workspace' : labelForView(shellView)} />
                      <InspectorRow label="Connection Status" value={isConnected ? 'Online' : 'Offline'} />
                    </div>
                  )
                )}
              </aside>
            )}
          </div>
        </section>

        <footer className="footer">
          <FooterItem label="Current Runtime Version" value={version} />
          <FooterItem label="Connection Status" value={isConnected ? 'Online' : 'Offline'} />
          <FooterItem label="Current Date" value={clock.toLocaleDateString()} />
          <FooterItem label="Live Time" value={clock.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} />
          <FooterItem label="Application Version" value="0.1.0" />
        </footer>
      </section>

      {commandPaletteOpen && (
        <CommandPalette
          query={commandQuery}
          version={version}
          onQueryChange={setCommandQuery}
          onClose={() => setCommandPaletteOpen(false)}
          onNavigate={(target) => {
            setShellView(commandTargetToView(target));
            setCommandPaletteOpen(false);
          }}
        />
      )}
    </main>
  );
}

function commandTargetToView(target: CommandTarget): ShellView {
  switch (target) {
    case 'agents-placeholder':
      return 'agents';
    case 'knowledge-placeholder':
      return 'knowledge';
    case 'memory-placeholder':
      return 'memory';
    default:
      return target;
  }
}

function isAiWorkspace(view: ShellView) {
  return view === 'agents' || view === 'workflows' || view === 'knowledge' || view === 'memory' || view === 'observability';
}

function labelForView(view: ShellView): string {
  switch (view) {
    case 'home':
      return 'Home';
    case 'chat':
      return 'Chat';
    case 'projects':
      return 'Projects';
    case 'goals':
      return 'Goals';
    case 'tasks':
      return 'Tasks';
    case 'agents':
      return 'Agents';
    case 'workflows':
      return 'Workflows';
    case 'knowledge':
      return 'Knowledge';
    case 'memory':
      return 'Memory';
    case 'observability':
      return 'Observability';
    case 'settings':
      return 'Settings';
    case 'about':
      return 'About';
  }
}

function NavButton(props: { active?: boolean; children: string; onClick: () => void }) {
  return (
    <button type="button" className={props.active ? 'nav-button active' : 'nav-button'} onClick={props.onClick}>
      {props.children}
    </button>
  );
}

function VersionSwitch({ value, onChange }: { value: Version; onChange: (value: Version) => void }) {
  return (
    <div className="pill-switch" aria-label="Version Switch">
      <button type="button" className={value === 'V1' ? 'active' : ''} onClick={() => onChange('V1')}>V1</button>
      <button type="button" className={value === 'V2' ? 'active' : ''} onClick={() => onChange('V2')}>V2</button>
    </div>
  );
}

function ThemeSwitch({ value, onChange }: { value: ThemeMode; onChange: (value: ThemeMode) => void }) {
  return (
    <button type="button" className="ghost" onClick={() => onChange(value === 'dark' ? 'light' : 'dark')}>
      Theme: {value}
    </button>
  );
}

function HomeView({ version }: { version: Version }) {
  const { user } = useAuth();
  const now = new Date();
  return (
    <div className="stack dashboard">
      <DashboardHeader version={version} />

      <section className="dashboard-section">
        <SectionHeading title="Workspace Summary" subtitle="Real backend data only" />
        <div className="dashboard-grid summary-grid">
          <DashboardMetric label="Workspace Name" value={version === 'V1' ? 'Traditional Workspace' : 'AI Operating System'} />
          <DashboardMetric label="Current Version" value={version} />
          <DashboardMetric label="Current User" value={user?.full_name || user?.email || "No user data available"} />
          <DashboardMetric label="Current Organization" value={user?.organization_id ? `Organization ID: ${user.organization_id}` : "No organization selected"} />
          <DashboardMetric label="Current Date" value={now.toLocaleDateString()} />
          <DashboardMetric label="Connection Status" value={navigator.onLine ? 'Online' : 'Offline'} />
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeading title="Quick Actions" subtitle="Navigation only" />
        <div className="dashboard-grid action-grid">
          <ActionCard title="New Project" description="Create a project workspace." />
          <ActionCard title="New Goal" description="Create a goal record." />
          <ActionCard title="New Task" description="Create a task item." />
          {version === 'V2' && <ActionCard title="Start Chat (V2)" description="Open the AI conversation workspace." />}
          {version === 'V2' && <ActionCard title="Create Agent (V2)" description="Open the agent workspace." />}
          {version === 'V2' && <ActionCard title="Upload Knowledge (V2)" description="Open the knowledge workspace." />}
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeading title="Projects" subtitle="Recent projects" />
        <div className="dashboard-grid content-grid">
          <Card title="Recent Projects" subtitle="No fake project names">
            <EmptyState label="No projects available." />
          </Card>
          <Card title="Project Actions" subtitle="Navigation only">
            <div className="inline-actions">
              <button type="button" className="ghost">Create Project</button>
              <button type="button" className="ghost">View All</button>
            </div>
          </Card>
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeading title="Goals" subtitle="Goals and status" />
        <Card title="Goals" subtitle="No fake goal data">
          <EmptyState label="No goals created." />
        </Card>
      </section>

      <section className="dashboard-section">
        <SectionHeading title="Tasks" subtitle="Assigned, pending, completed" />
        <div className="dashboard-grid summary-grid">
          <DashboardMetric label="Assigned Tasks" value="No tasks available" />
          <DashboardMetric label="Pending Tasks" value="No tasks available" />
          <DashboardMetric label="Completed Tasks" value="No tasks available" />
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeading title="Recent Activity" subtitle="Live backend events only" />
        <Card title="Activity Feed" subtitle="No fabricated logs">
          <EmptyState label="No recent activity." />
        </Card>
      </section>

      <section className="dashboard-section">
        <SectionHeading title="Runtime Panel" subtitle="Simple right-side inspector values mirrored in the dashboard" />
        <div className="dashboard-grid summary-grid">
          <DashboardMetric label="Runtime Version" value={version} />
          <DashboardMetric label="Workspace" value={version === 'V1' ? 'Traditional Workspace' : 'AI Operating System'} />
          <DashboardMetric label="Selected Project" value="No project selected" />
          <DashboardMetric label="Selected Page" value="Home" />
          <DashboardMetric label="Connection Status" value={navigator.onLine ? 'Online' : 'Offline'} />
        </div>
      </section>
    </div>
  );
}

function ChatView({ version, state }: { version: Version; state: WorkspaceState }) {
  return (
    <div className="stack">
      <Card title="AI Chat" subtitle="V2 only">
        <div className="chat-layout">
          <div className="chat-column">
            <section className="chat-list card-surface">
              <h4>Conversation List</h4>
              <EmptyState label={state === 'empty' ? 'No conversations connected.' : state === 'loading' ? 'Loading conversations.' : 'Unable to load conversations.'} />
            </section>
            <section className="chat-window card-surface">
              <h4>Chat Window</h4>
              <EmptyState label={state === 'empty' ? 'No conversation selected.' : state === 'loading' ? 'Loading chat window.' : 'Chat is unavailable right now.'} />
            </section>
            <section className="chat-input card-surface">
              <h4>Input Area</h4>
              <input className="search" placeholder="Prompt input" aria-label="Prompt input" />
              <div className="inline-actions">
                <button type="button" className="ghost">Attachment</button>
                <button type="button" className="ghost">New Chat</button>
                <button type="button" className="ghost">Clear Chat</button>
              </div>
            </section>
          </div>

          <aside className="chat-context card-surface">
            <h4>Right Context Panel</h4>
            <InspectorRow label="Current Project" value="No project selected" />
            <InspectorRow label="Current Goal" value="No goal selected" />
            <InspectorRow label="Current Task" value="No task selected" />
            <InspectorRow label="Runtime Version" value={version} />
            <InspectorRow label="Connection Status" value={navigator.onLine ? 'Online' : 'Offline'} />
          </aside>
        </div>
      </Card>
    </div>
  );
}

function GoalsView({ state }: { state: WorkspaceState }) {
  return (
    <div className="stack">
      <Card title="Goals" subtitle="Day-to-day workspace">
        <div className="workspace-toolbar">
          <button type="button" className="primary">New Goal</button>
          <button type="button" className="ghost">Edit</button>
          <button type="button" className="ghost">Archive</button>
          <button type="button" className="ghost">Delete</button>
        </div>
        <div className="workspace-columns">
          <Card title="Goal List" subtitle="No fake goals">
            {renderWorkspaceState(state, 'No goals available.')}
          </Card>
          <Card title="Goal Details" subtitle="Placeholder details only">
            {renderWorkspaceState(state, 'Select a goal to inspect status, priority, progress, milestones, and related project.')}
          </Card>
        </div>
        <div className="workspace-columns compact">
          <DashboardMetric label="Status" value="No goal selected" />
          <DashboardMetric label="Priority" value="No priority selected" />
          <DashboardMetric label="Progress" value="No progress available" />
          <DashboardMetric label="Related Project" value="No related project selected" />
        </div>
        <Card title="Milestones" subtitle="Timeline placeholders only">
          <EmptyState label="No milestone dates available." />
        </Card>
      </Card>
    </div>
  );
}

function TasksView({ state }: { state: WorkspaceState }) {
  return (
    <div className="stack">
      <Card title="Tasks" subtitle="Workspace views">
        <div className="workspace-toolbar">
          <button type="button" className="primary">New Task</button>
          <button type="button" className="ghost">Timeline</button>
          <button type="button" className="ghost">Board</button>
          <button type="button" className="ghost">List</button>
        </div>
        <div className="task-view-grid">
          <Card title="List View" subtitle="Task list">
            {renderWorkspaceState(state, 'No tasks available.')}
          </Card>
          <Card title="Board View" subtitle="Kanban">
            {renderWorkspaceState(state, 'No task cards available for the board view.')}
          </Card>
          <Card title="Timeline View" subtitle="Simple timeline placeholder">
            {renderWorkspaceState(state, 'No timeline entries available.')}
          </Card>
        </div>
        <Card title="Task Dependencies" subtitle="Relationship visualization">
          <EmptyState label="No dependency relationships available." />
        </Card>
      </Card>
    </div>
  );
}

function EnterprisePlatformView({
  section,
  onSectionChange,
}: {
  section: PlatformSection;
  onSectionChange: (value: PlatformSection) => void;
}) {
  return (
    <div className="stack enterprise-platform">
      <section className="card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">Enterprise Platform</p>
            <h3>Operations Center</h3>
            <p className="muted">Runtime observability, architecture, execution timeline, and runtime graph views are connected here.</p>
          </div>
        </div>
        <div className="section-tabs">
          <TabButton active={section === 'observability'} onClick={() => onSectionChange('observability')}>Runtime Observability</TabButton>
          <TabButton active={section === 'architecture'} onClick={() => onSectionChange('architecture')}>Live Architecture</TabButton>
          <TabButton active={section === 'timeline'} onClick={() => onSectionChange('timeline')}>Execution Timeline</TabButton>
        </div>
      </section>

      {section === 'observability' && <ObservabilityView />}
      {section === 'architecture' && <ArchitectureView />}
      {section === 'timeline' && <ExecutionTimelineView />}
    </div>
  );
}

function ObservabilityView() {
  return (
    <div className="stack">
      <div className="platform-grid">
        <Card title="Runtime Overview" subtitle="No fake runtime values">
          <EmptyState label="Runtime overview data is unavailable." />
        </Card>
        <Card title="Current Runtime" subtitle="Execution context">
          <EmptyState label="No runtime instance selected." />
        </Card>
        <Card title="Current Version" subtitle="Version context">
          <EmptyState label="No version context available." />
        </Card>
        <Card title="Health Status" subtitle="Connected components">
          <EmptyState label="No health data available." />
        </Card>
      </div>
      <div className="platform-grid two-up">
        <Card title="Execution Timeline" subtitle="Lifecycle view">
          <EmptyState label="No execution timeline data available." />
        </Card>
        <Card title="Execution Trace" subtitle="Trace placeholder">
          <EmptyState label="No execution trace available." />
        </Card>
      </div>
      <Card title="Pipeline Stages" subtitle="Placeholder stages only">
        <StageFlow />
      </Card>
    </div>
  );
}

function ArchitectureView() {
  const nodes = ['Frontend', 'Backend', 'API', 'Runtime', 'Execution Engine', 'Agents', 'Memory', 'Knowledge', 'Workflow', 'Provider', 'Database', 'Observability'];
  return (
    <div className="stack">
      <Card title="Live Architecture View" subtitle="Connected relationships">
        <div className="architecture-map">
          {nodes.map((node, index) => (
            <div key={node} className={index === 3 ? 'architecture-node active' : 'architecture-node'}>
              <strong>{node}</strong>
              {index < nodes.length - 1 && <span className="architecture-line" aria-hidden="true" />}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function ExecutionTimelineView() {
  const stages = [
    'Governance',
    'Context',
    'Planning',
    'Execution',
    'Reflection',
    'Evaluation',
    'Learning',
    'Adaptive Planning',
    'Long-Term Intelligence',
    'Optimization',
    'Completed',
  ];

  return (
    <Card title="Execution Timeline" subtitle="Lifecycle stages">
      <div className="timeline-stack">
        {stages.map((stage, index) => (
          <div key={stage} className="timeline-row">
            <div className="timeline-marker">{index + 1}</div>
            <div className="timeline-label">{stage}</div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function StageFlow() {
  const stages = ['Governance', 'Context', 'Planning', 'Execution', 'Reflection', 'Evaluation', 'Learning', 'Adaptive Planning', 'Long-Term Intelligence', 'Optimization', 'Completed'];
  return (
    <div className="timeline-stack">
      {stages.map((stage, index) => (
        <div key={stage} className="timeline-row">
          <div className="timeline-marker">{index + 1}</div>
          <div className="timeline-label">{stage}</div>
        </div>
      ))}
    </div>
  );
}

function SettingsView({
  version,
  section,
  onSectionChange,
}: {
  version: Version;
  section: SettingsSection;
  onSectionChange: (value: SettingsSection) => void;
}) {
  return (
    <div className="stack settings-center">
      <section className="card">
        <div className="card-heading">
          <div>
            <p className="eyebrow">Settings</p>
            <h3>Workspace Administration</h3>
            <p className="muted">General, appearance, runtime, AI, security, profile, workspace, version, organizations, and integrations live here.</p>
          </div>
        </div>
        <div className="section-tabs settings-tabs">
          {(['general', 'appearance', 'notifications', 'runtime', 'ai', 'security', 'profile', 'workspace', 'version', 'organizations', 'integrations'] as SettingsSection[]).map((item) => (
            <TabButton key={item} active={section === item} onClick={() => onSectionChange(item)}>
              {sectionLabel(item)}
            </TabButton>
          ))}
        </div>
      </section>

      <div className="platform-grid two-up">
        <Card title="Form Panel" subtitle={sectionLabel(section)}>
          <SettingsForm section={section} version={version} />
        </Card>
        <Card title="Summary Panel" subtitle="Connected placeholder surface">
          {section === 'organizations' ? <EmptyState label="No organization data available." /> : section === 'security' ? <EmptyState label="No security configuration loaded." /> : section === 'integrations' ? <EmptyState label="No integrations connected." /> : <EmptyState label="No settings data available." />}
        </Card>
      </div>
    </div>
  );
}

function AboutView({ section, onSectionChange }: { section: string; onSectionChange: (value: string) => void }) {
  const sections = [
    'overview',
    'getting-started',
    'architecture',
    'runtime',
    'execution-flow',
    'ai-pipeline',
    'project-structure',
    'frontend',
    'backend',
    'database',
    'technology-stack',
    'v1-vs-v2',
    'roles',
    'security',
    'governance',
    'memory',
    'knowledge',
    'agents',
    'workflow',
    'observability',
    'deployment',
    'api-overview',
    'faq',
  ];

  return (
    <article className="about docs-center">
      <aside className="docs-sidebar card">
        <p className="eyebrow">Documentation</p>
        <div className="docs-nav">
          {sections.map((item) => (
            <TabButton key={item} active={section === item} onClick={() => onSectionChange(item)}>
              {sectionLabel(item)}
            </TabButton>
          ))}
        </div>
      </aside>
      <section className="docs-content card">
        <h3>{sectionLabel(section)}</h3>
        <p className="muted">Technical documentation center for new users and developers.</p>
        <div className="doc-grid docs-grid">
          <DocBlock title="Overview" body="AgentCorp is an enterprise platform with connected workspace, AI, runtime, and operations layers." />
          <DocBlock title="Getting Started" body="Use the shell navigation, version switch, and documentation sidebar to move between connected areas." />
          <DocBlock title="Architecture" body="The system spans frontend, backend, API, runtime, execution, data, and operational surfaces." />
          <DocBlock title="Runtime" body="Runtime context connects execution, orchestration, and platform state without fabricated values." />
          <DocBlock title="Execution Flow" body="Execution flows from governance through context, planning, execution, reflection, evaluation, learning, and optimization." />
          <DocBlock title="AI Pipeline" body="The AI pipeline connects agents, workflows, memory, knowledge, and tools under runtime control." />
          <DocBlock title="Project Structure" body="The codebase separates frontend, backend, tests, docs, and operational helpers." />
          <DocBlock title="Frontend" body="The frontend uses React, TypeScript, and Vite with a shared enterprise design system." />
          <DocBlock title="Backend" body="The backend exposes service, schema, and runtime layers for platform coordination." />
          <DocBlock title="Database" body="Database design supports platform state, entities, and runtime records without demo data." />
          <DocBlock title="Technology Stack" body="The stack is centered on React, TypeScript, Python, and structured services." />
          <DocBlock title="V1 vs V2" body="V1 is a traditional workspace. V2 adds AI, runtime, workflows, memory, and observability." />
          <DocBlock title="Roles" body="Roles distinguish users, operators, administrators, and runtime-aware AI entities." />
          <DocBlock title="Security" body="Security covers authentication, RBAC, API access, auditability, and policy enforcement." />
          <DocBlock title="Governance" body="Governance defines policy, control, and execution boundaries across the platform." />
          <DocBlock title="Memory" body="Memory is treated as connected contextual storage rather than freeform chat history." />
          <DocBlock title="Knowledge" body="Knowledge is organized as searchable and assignable workspace context." />
          <DocBlock title="Agents" body="Agents coordinate execution as part of the broader AI operating model." />
          <DocBlock title="Workflow" body="Workflows define structured orchestration, branching, and execution direction." />
          <DocBlock title="Observability" body="Observability surfaces runtime state, traces, and execution context." />
          <DocBlock title="Deployment" body="Deployment guidance should reflect the production topology and runtime services." />
          <DocBlock title="API Overview" body="API surfaces connect the frontend to workspace, runtime, and administrative services." />
          <DocBlock title="FAQ" body="Use empty states, loading states, and error states wherever backend data is unavailable." />
        </div>
      </section>
    </article>
  );
}

function renderWorkspaceState(state: WorkspaceState, emptyLabel: string) {
  if (state === 'loading') return <LoadingState label="Loading workspace data." />;
  if (state === 'error') return <ErrorState label="Workspace data is unavailable." />;
  return <EmptyState label={emptyLabel} />;
}

function AgentsView({ state }: { state: WorkspaceState }) {
  return (
    <div className="stack ai-workspace">
      <section className="ai-header card">
        <div>
          <p className="eyebrow">Agents</p>
          <h3>Enterprise Agents Workspace</h3>
          <p className="muted">Agent profiles, assignments, and execution relationships stay connected to the broader control center.</p>
        </div>
      </section>
      <div className="ai-grid">
        <Card title="Agent List" subtitle="No fake agents">
          {renderWorkspaceState(state, 'No agents available.')}
        </Card>
        <Card title="Agent Details" subtitle="Selection required">
          {renderWorkspaceState(state, 'Select an agent to inspect details.')}
        </Card>
      </div>
      <div className="ai-grid three-up">
        <Card title="Capabilities" subtitle="Declared capabilities only">
          {renderWorkspaceState(state, 'No capability data available.')}
        </Card>
        <Card title="Assignments" subtitle="Project, workflow, knowledge, and memory">
          {renderWorkspaceState(state, 'No assignment data available.')}
        </Card>
        <Card title="Relationship Panel" subtitle="Connected entities">
          <EntityChain />
        </Card>
      </div>
    </div>
  );
}

function WorkflowBuilderView({
  state,
  selectedNode,
  onSelectNode,
}: {
  state: WorkspaceState;
  selectedNode: string | null;
  onSelectNode: (value: string | null) => void;
}) {
  return (
    <div className="stack ai-workspace">
      <section className="ai-header card">
        <div>
          <p className="eyebrow">Workflow Builder</p>
          <h3>Enterprise Orchestration Canvas</h3>
          <p className="muted">Blocks, relationships, execution direction, nested groups, and parallel branches are shown as a connected orchestration surface.</p>
        </div>
      </section>
      <section className="workflow-canvas card">
        <div className="workflow-row">
          <WorkflowBlock label="Start" active={selectedNode === 'Start'} onClick={() => onSelectNode('Start')} />
          <WorkflowConnector />
          <WorkflowBlock label="Goal" active={selectedNode === 'Goal'} onClick={() => onSelectNode('Goal')} />
          <WorkflowConnector />
          <WorkflowBlock label="Task" active={selectedNode === 'Task'} onClick={() => onSelectNode('Task')} />
          <WorkflowConnector />
          <WorkflowBlock label="Agent" active={selectedNode === 'Agent'} onClick={() => onSelectNode('Agent')} />
          <WorkflowConnector />
          <WorkflowBlock label="Runtime" active={selectedNode === 'Runtime'} onClick={() => onSelectNode('Runtime')} />
          <WorkflowConnector />
          <WorkflowBlock label="End" active={selectedNode === 'End'} onClick={() => onSelectNode('End')} />
        </div>
        <div className="workflow-branches">
          <div className="workflow-group">
            <h4>Nested Workflow Group</h4>
            <div className="workflow-row compact">
              <WorkflowBlock label="Knowledge" active={selectedNode === 'Knowledge'} onClick={() => onSelectNode('Knowledge')} />
              <WorkflowConnector />
              <WorkflowBlock label="Memory" active={selectedNode === 'Memory'} onClick={() => onSelectNode('Memory')} />
              <WorkflowConnector />
              <WorkflowBlock label="Tool" active={selectedNode === 'Tool'} onClick={() => onSelectNode('Tool')} />
            </div>
          </div>
          <div className="workflow-group">
            <h4>Parallel Branches</h4>
            <div className="workflow-parallel">
              <WorkflowBlock label="Decision" active={selectedNode === 'Decision'} onClick={() => onSelectNode('Decision')} />
              <WorkflowBlock label="Approval" active={selectedNode === 'Approval'} onClick={() => onSelectNode('Approval')} />
              <WorkflowBlock label="Reflection" active={selectedNode === 'Reflection'} onClick={() => onSelectNode('Reflection')} />
              <WorkflowBlock label="Evaluation" active={selectedNode === 'Evaluation'} onClick={() => onSelectNode('Evaluation')} />
              <WorkflowBlock label="Learning" active={selectedNode === 'Learning'} onClick={() => onSelectNode('Learning')} />
            </div>
          </div>
        </div>
        {state === 'empty' ? <EmptyState label="No workflow execution data available. Select a block to inspect the placeholder path." /> : renderWorkspaceState(state, 'No workflow data available.') }
      </section>
    </div>
  );
}

function KnowledgeView({ state }: { state: WorkspaceState }) {
  return (
    <div className="stack ai-workspace">
      <section className="ai-header card">
        <div>
          <p className="eyebrow">Knowledge Base</p>
          <h3>Knowledge Workspace</h3>
          <p className="muted">Collections, documents, categories, and relationships connect to project assignments and search.</p>
        </div>
      </section>
      <div className="ai-grid">
        <Card title="Collections" subtitle="Structured knowledge groups">{renderWorkspaceState(state, 'No collections available.')}</Card>
        <Card title="Documents" subtitle="No fake documents">{renderWorkspaceState(state, 'No documents available.')}</Card>
      </div>
      <div className="ai-grid three-up">
        <Card title="Categories" subtitle="Classification">{renderWorkspaceState(state, 'No categories available.')}</Card>
        <Card title="Relationships" subtitle="Connected context">{renderWorkspaceState(state, 'No relationship data available.')}</Card>
        <Card title="Preview Panel" subtitle="Read-only preview">{renderWorkspaceState(state, 'Select a document to preview it.')}</Card>
      </div>
    </div>
  );
}

function MemoryView({ state }: { state: WorkspaceState }) {
  return (
    <div className="stack ai-workspace">
      <section className="ai-header card">
        <div>
          <p className="eyebrow">Memory Explorer</p>
          <h3>Memory Workspace</h3>
          <p className="muted">Short-term, long-term, conversation, and project memory are surfaced together with relationship and timeline context.</p>
        </div>
      </section>
      <div className="ai-grid three-up">
        <Card title="Short-Term Memory" subtitle="Ephemeral context">{renderWorkspaceState(state, 'No short-term memory entries available.')}</Card>
        <Card title="Long-Term Memory" subtitle="Persistent context">{renderWorkspaceState(state, 'No long-term memory entries available.')}</Card>
        <Card title="Conversation Memory" subtitle="Dialogue context">{renderWorkspaceState(state, 'No conversation memory entries available.')}</Card>
      </div>
      <div className="ai-grid">
        <Card title="Project Memory" subtitle="Project-linked context">{renderWorkspaceState(state, 'No project memory entries available.')}</Card>
        <Card title="Memory Relationships" subtitle="Connected references">{renderWorkspaceState(state, 'No memory relationships available.')}</Card>
        <Card title="Memory Timeline" subtitle="Timeline placeholder">{renderWorkspaceState(state, 'No memory timeline entries available.')}</Card>
      </div>
    </div>
  );
}

function ToolRegistryView({ state }: { state: WorkspaceState }) {
  return (
    <div className="stack ai-workspace">
      <section className="ai-header card">
        <div>
          <p className="eyebrow">Tool Registry</p>
          <h3>Execution Tool Workspace</h3>
          <p className="muted">Installed tools, available tools, capabilities, categories, and project assignment stay visible in one place.</p>
        </div>
      </section>
      <div className="ai-grid">
        <Card title="Installed Tools" subtitle="Active registry">{renderWorkspaceState(state, 'No installed tools available.')}</Card>
        <Card title="Available Tools" subtitle="Connectable tools">{renderWorkspaceState(state, 'No available tools available.')}</Card>
      </div>
      <div className="ai-grid three-up">
        <Card title="Capability" subtitle="Supported action sets">{renderWorkspaceState(state, 'No capability data available.')}</Card>
        <Card title="Category" subtitle="Tool grouping">{renderWorkspaceState(state, 'No category data available.')}</Card>
        <Card title="Tool Details" subtitle="Read-only details">{renderWorkspaceState(state, 'Select a tool to view details.')}</Card>
      </div>
    </div>
  );
}

function WorkflowBlock({ label, active, onClick }: { label: string; active?: boolean; onClick: () => void }) {
  return (
    <button type="button" className={active ? 'workflow-block active' : 'workflow-block'} onClick={onClick}>
      {label}
    </button>
  );
}

function WorkflowConnector() {
  return <div className="workflow-connector" aria-hidden="true" />;
}

function EntityChain() {
  const items = ['Project', 'Goals', 'Tasks', 'Workflow', 'Agents', 'Knowledge', 'Memory', 'Tools', 'Execution'];
  return (
    <div className="entity-chain" aria-label="Entity relationships">
      {items.map((item, index) => (
        <div key={item} className="entity-step">
          <div className="entity-node">{item}</div>
          {index < items.length - 1 && <div className="entity-arrow">↓</div>}
        </div>
      ))}
    </div>
  );
}

function SettingsForm({ section, version }: { section: SettingsSection; version: Version }) {
  if (section === 'organizations' || section === 'security' || section === 'integrations') {
    return <EmptyState label="No form data available for this section." />;
  }

  return (
    <div className="settings-form">
      <label>
        {sectionLabel(section)}
        <input className="search" placeholder="No backend data available" />
      </label>
      <label>
        Version
        <input className="search" value={version} readOnly />
      </label>
    </div>
  );
}

function sectionLabel(section: string) {
  return section
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function TabButton(props: { active?: boolean; children: string; onClick: () => void }) {
  return (
    <button type="button" className={props.active ? 'tab-button active' : 'tab-button'} onClick={props.onClick}>
      {props.children}
    </button>
  );
}

function CommandPalette(props: {
  query: string;
  version: Version;
  onQueryChange: (value: string) => void;
  onClose: () => void;
  onNavigate: (target: CommandTarget) => void;
}) {
  const commands = useMemo(() => {
    const items: Array<{ label: string; target: CommandTarget }> = [
      { label: 'Projects', target: 'projects' },
      { label: 'Goals', target: 'goals' },
      { label: 'Tasks', target: 'tasks' },
      { label: 'Chat', target: 'chat' },
      { label: 'Settings', target: 'settings' },
      { label: 'About', target: 'about' },
    ];
    if (props.version === 'V2') {
      items.splice(4, 0, { label: 'Agents', target: 'agents-placeholder' }, { label: 'Knowledge', target: 'knowledge-placeholder' }, { label: 'Memory', target: 'memory-placeholder' });
    }
    return items.filter((item) => item.label.toLowerCase().includes(props.query.toLowerCase()));
  }, [props.query, props.version]);

  return (
    <div className="command-palette-backdrop" onClick={props.onClose}>
      <section className="command-palette" onClick={(event) => event.stopPropagation()}>
        <input
          className="search"
          value={props.query}
          onChange={(event) => props.onQueryChange(event.target.value)}
          placeholder="Search workspace"
          aria-label="Search workspace"
          autoFocus
        />
        <div className="command-list">
          {commands.length === 0 ? (
            <EmptyState label="No matching commands." />
          ) : (
            commands.map((command) => (
              <button key={command.label} type="button" className="command-item" onClick={() => props.onNavigate(command.target)}>
                {command.label}
              </button>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function DashboardHeader({ version }: { version: Version }) {
  return (
    <section className="dashboard-header">
      <div>
        <p className="eyebrow">Dashboard</p>
        <h3>Workspace Overview</h3>
        <p className="muted">{version === 'V1' ? 'Traditional enterprise workspace overview.' : 'AI-native workspace overview.'}</p>
      </div>
      <div className="dashboard-header-actions">
        <button type="button" className="primary">New Project</button>
        <button type="button" className="ghost">Refresh</button>
      </div>
    </section>
  );
}

function SectionHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="section-heading">
      <div>
        <h4>{title}</h4>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

function DashboardMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ActionCard({ title, description }: { title: string; description: string }) {
  return (
    <button type="button" className="action-card" aria-label={title}>
      <strong>{title}</strong>
      <span>{description}</span>
    </button>
  );
}

function Card(props: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <h3>{props.title}</h3>
          <p>{props.subtitle}</p>
        </div>
      </div>
      {props.children}
    </section>
  );
}

function DocBlock(props: { title: string; body: string }) {
  return (
    <section className="doc-block">
      <h4>{props.title}</h4>
      <p>{props.body}</p>
    </section>
  );
}

function DrawerSection(props: { title: string; body: string }) {
  return (
    <section className="drawer-section">
      <h5>{props.title}</h5>
      <p>{props.body}</p>
    </section>
  );
}

function EmptyState({ label }: { label: string }) {
  return <div className="empty-state">{label}</div>;
}

function LoadingState({ label }: { label: string }) {
  return <div className="state-box state-loading">{label}</div>;
}

function ErrorState({ label }: { label: string }) {
  return <div className="state-box state-error">{label}</div>;
}

function InspectorRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="inspector-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function FooterItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="footer-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
