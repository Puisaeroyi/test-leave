# Leave Management System - Frontend

React 18 + TypeScript + Vite + Tailwind CSS frontend for the Leave Management System.

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | React | 18 |
| **Language** | TypeScript | Latest |
| **Build Tool** | Vite | Latest |
| **Styling** | Tailwind CSS | 4.x |
| **Routing** | React Router | 7.x |

## Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── LoginPage.tsx      # Login with username/password
│   │   └── OnboardingPage.tsx # 4-step onboarding wizard
│   ├── components/            # Reusable components (to be added)
│   ├── hooks/                 # Custom hooks (to be added)
│   ├── App.tsx                # Main app with routing logic
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles with Tailwind
├── public/                    # Static assets
├── index.html                 # HTML template
├── vite.config.ts             # Vite configuration
├── tailwind.config.js         # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
└── package.json               # Dependencies
```

## Setup Instructions

### Prerequisites

- Node.js 20+ (Note: Current environment has Node 18.19.1, which works but shows warnings)

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Visit `http://localhost:5173`

### Build

```bash
npm run build
```

Output is in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Pages

### Login Page

- Username/password authentication form
- Loading state during authentication
- Error handling and validation
- "Forgot password" link (placeholder)
- Responsive design with gradient background

**Features:**
- Clean, modern UI with Tailwind CSS
- Form validation
- Loading spinner during submission
- Error message display

### Onboarding Page

4-step wizard for new users:

1. **Step 1:** Enter Full Name
2. **Step 2:** Select Entity (Organization)
3. **Step 3:** Select Location (filtered by Entity)
4. **Step 4:** Select Department (filtered by Entity)

**Features:**
- Progress bar with step indicator
- Cascade dropdowns (Entity → Location → Department)
- Location dropdown is blurred/disabled until Entity is selected
- Info cards showing selected values
- Back/Next navigation
- Validation at each step
- Skip option
- Responsive design

## Mock Data

The onboarding page uses mock data for demonstration:

- **3 Entities:** Acme Corporation, Tech Innovations Inc, Global Solutions Ltd
- **2 Locations per Entity:** Various cities (HCMC, Singapore, New York, etc.)
- **2-3 Departments per Entity:** Engineering, HR, Finance, Product, Marketing, etc.

Replace mock data with API calls in production.

## State Management

Currently using React's `useState` for local state. Authentication state is managed in `App.tsx`:

```typescript
- showOnboarding: boolean
- isLoading: boolean
```

Onboarding completion is stored in `localStorage` for demo purposes.

## Next Steps

1. **API Integration:** Replace mock data with actual API calls
2. **Form Validation:** Add more robust validation
3. **Error Handling:** Implement proper error boundaries
4. **Loading States:** Add skeleton loaders for better UX
5. **Dashboard:** Create the main dashboard page
6. **Authentication:** Implement OAuth (Google/Microsoft)
7. **Testing:** Add unit tests with Vitest
8. **E2E Testing:** Add Playwright or Cypress tests

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Notes

- Path aliases configured: `@/*` → `./src/*`
- Tailwind CSS with custom primary color scheme
- TypeScript strict mode enabled
- All pages are fully responsive
