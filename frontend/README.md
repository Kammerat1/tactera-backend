# Tactera Frontend

React TypeScript frontend for the Tactera football management game.

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
cd frontend
npm install
```

## Running

### Development Server
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/   # React components
│   ├── pages/        # Page components
│   ├── hooks/        # Custom React hooks
│   ├── utils/        # Utility functions
│   └── types/        # TypeScript type definitions
├── public/           # Static assets
└── package.json      # Dependencies and scripts
```

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Lucide React** - Icon library

## Development

### Linting
```bash
npm run lint
```

### Environment Variables
Create a `.env` file in the frontend directory:
```
VITE_API_URL=http://localhost:8000
```