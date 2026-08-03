# AgentCorp Frontend

AgentCorp Frontend is the enterprise web application for the AgentCorp platform. It provides the authenticated shell, versioned workspace experience, and the product surfaces for V1 and V2 capabilities.

## Technology Stack

- React
- TypeScript
- Vite
- CSS custom properties and responsive layouts

## Folder Structure

- `src/main.tsx` - application entry point
- `src/ui/App.tsx` - shell, navigation, and workspace rendering
- `src/styles.css` - shared design system and responsive styling
- `index.html` - Vite entry document

## Installation

From the frontend directory:

```bash
npm install
```

## Development

Run the local development server:

```bash
npm run dev
```

## Build

Create a production build:

```bash
npm run build
```

## Version Overview

### V1

V1 is the traditional enterprise workspace. It keeps the classic workspace structure and excludes AI-native capabilities.

### V2

V2 includes the AI operating system surfaces, including AI chat, agents, workflows, knowledge, memory, runtime, and observability.

## Project Architecture

The frontend uses a shared shell with version-aware navigation and workspace panels. Each major workspace is rendered as a connected enterprise surface and uses the same design system for spacing, cards, forms, and empty states.

## Contribution Guide

- Keep changes scoped to the current workspace or feature area.
- Reuse the existing design system and component patterns.
- Avoid fabricated data, demo analytics, and decorative UI.
- Run the production build before finishing a change.

## License

Refer to the repository-level license for usage and distribution terms.
