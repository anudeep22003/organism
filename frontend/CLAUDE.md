This project is going to leverage the app of apps idea and build a github repo teardown app. The sequence of things this app does is:
- The user should be able to enter a github repo url
  - You want to validate the url, make sure it is a valid github repo url (use regex and/or zod if required)
  - once validated, check that it is a public repo (if not, let the user know)
  - once validated, a pill or badge in the input area should be shown to indicate that the repo is valid, and only then should the submit button be enabled
- The user should be able to click a button to submit the repo url
- Once the repo is submitted, it kicks of a series of steps on the backend that clones the repo, and runs claude code sdk on it with a prewritten prompt to teardown the repo, understand what data structures are used, mermaid diagrams to show the flow and sequence, etc. 
  - While processing the steps that the sdk is taking should show via the `@ClaudeMessage` component on the right in the generative area
- The final output after the teardown is complete will be a markdown file with a detailed writeup. Use the `@WriterMessage` component to show this output.


----
I cloned the app of apps monorepo. You are in the frontend folder. 

# Claude Code SDK Interface

## Available Architecture & Components

### Core State Management
- **Zustand Store** (`useMessageStore`): Centralized state for messages, streaming actors, and tab management
- **App Context** (`AppContext`): Global app state including input text, generative area visibility, and message handling
- **Socket Integration** (`useSocket`): Pre-configured WebSocket client with real-time streaming support

### Message System
- **Message Types**: `human`, `assistant`, `coder`, `writer`, `claude`
- **Streaming Support**: Real-time message updates with delta-based content streaming
- **Actor Registry**: Extensible system for different message types with custom renderers
- **Message Store Hooks**: 
  - `useHumanMessages()`, `useAssistantMessages()`, `useCodeMessages()`, `useWriterMessages()`, `useClaudeMessages()`
  - `useAvailableActors()` - Get all active actor types
  - `useHumanAreaMessages()` - Combined human/assistant messages

### UI Components (shadcn/ui + Tailwind)
**Available Components:**
- `Button` - Multiple variants (default, destructive, outline, secondary, ghost, link) and sizes
- `Card` - Complete card system with header, content, footer, title, description, action
- `Tabs` - Full tab system with list, trigger, and content
- `Badge` - Status indicators with variants (default, secondary, destructive, outline)
- `Chart` - Recharts integration with tooltips, legends, and responsive containers

**Styling:**
- Tailwind CSS fully configured
- Dark theme optimized (black/white minimal aesthetic)
- Custom utility function `cn()` for class merging
- Consistent spacing, typography, and color system

### Markdown Rendering
- **MarkdownRenderer**: Full-featured markdown with syntax highlighting
- **Features**: Code blocks, Mermaid diagrams, tables, lists, links with previews
- **Syntax Highlighting**: VS Code Dark Plus theme
- **Mermaid Support**: Automatic diagram rendering with dark theme

### Socket Communication
**Available Events:**
- `c2s.coder.stream.start` - Start code generation stream
- `s2c.{actor}.stream.chunk` - Receive streaming content
- `s2c.{actor}.stream.end` - End streaming for actor
- `write_tsx_and_add_route` - Install generated app as new route

**Envelope Structure:**
```typescript
{
  v: "1",
  id: string,
  ts: number,
  requestId?: string,
  streamId?: string,
  direction: "c2s" | "s2c",
  actor: "assistant" | "coder" | "writer" | "claude",
  action: "stream",
  modifier: "start" | "chunk" | "end",
  data: T
}
```

### Available Libraries
**Core Dependencies:**
- `react` (19.1.1) - React framework
- `react-dom` (19.1.1) - DOM rendering
- `react-router` (7.8.0) - Client-side routing
- `socket.io-client` (4.8.1) - WebSocket communication
- `zustand` (5.0.8) - State management
- `zod` (4.0.17) - Schema validation
- `axios` (1.11.0) - HTTP client

**UI & Styling:**
- `@radix-ui/react-*` - Headless UI primitives
- `tailwindcss` (4.1.11) - Utility-first CSS
- `class-variance-authority` - Component variants
- `clsx` + `tailwind-merge` - Class name utilities

**Content & Visualization:**
- `react-markdown` (10.1.0) - Markdown rendering
- `react-syntax-highlighter` (15.6.3) - Code syntax highlighting
- `mermaid` (11.10.1) - Diagram rendering
- `recharts` (2.15.4) - Chart components
- `remark-gfm` (4.0.1) - GitHub Flavored Markdown

**Development:**
- `typescript` (5.8.3) - Type safety
- `vite` (7.1.0) - Build tool
- `eslint` (9.32.0) - Code linting

### Key Patterns & Conventions
1. **TypeScript First**: All components are fully typed with strict type checking
2. **Atomic Components**: Single responsibility, composable UI components
3. **Streaming Architecture**: Real-time updates with delta-based content streaming
4. **Actor Pattern**: Extensible message types with custom renderers
5. **Minimal Aesthetic**: Black/white theme with subtle gradients only when necessary
6. **Modular Design**: Clean separation of concerns, easy to extend

### Development Guidelines
- Use existing components before creating new ones
- Install additional shadcn/ui components as needed: `npx shadcn@latest add [component]`
- Follow the established patterns for state management and message handling
- Maintain the minimal black/white aesthetic
- Leverage the streaming architecture for real-time updates
- Use TypeScript for all new code with proper type definitions

Use bun for package manager. 


Use good coding principles, and good ui design principles:
- Do not repeat yourself
- premature optimization is the root of all evil
- Introduce the minimum number of changes to achieve the desired task
- Code should be self-documenting, no comments unless necessary
- All names should be descriptive and meaningful and read like elegant prose in the stacktrace
- Use the most specific type possible, try your hardest not to use `Any`
- files should not be longer than 200 lines of code

- I use bun for packlage management