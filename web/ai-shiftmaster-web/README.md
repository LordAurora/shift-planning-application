# ShiftMaster AI - Frontend

AI-powered shift planning web application built with Next.js and Ant Design.

## Tech Stack

- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **UI Library:** Ant Design (Enterprise UI)
- **State Management:** Zustand
- **HTTP Client:** Axios
- **Styling:** CSS (Corporate neutral colors)

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your API URL if needed
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@example.com | admin123 |
| Manager | manager@example.com | manager123 |
| Employee | employee@example.com | employee123 |

## Features

- **Authentication:** JWT-based login/logout with role-based access
- **Dashboard:** Overview statistics and quick actions
- **Employee Management:** CRUD operations, availability, working limits
- **Shift Management:** Weekly/monthly views, conflict detection
- **Shift Rules:** Define department-specific shift requirements
- **AI Optimization:** Generate optimal shift schedules
- **Notifications:** Real-time notification panel

## Project Structure

```
app/
├── components/        # Reusable UI components
├── lib/              # API client and services
├── store/            # Zustand state stores
├── theme/            # Ant Design theme configuration
├── types/            # TypeScript type definitions
├── login/            # Login page
├── dashboard/        # Dashboard page
├── employees/        # Employee management
├── shifts/           # Shift management
├── rules/            # Shift rules
├── ai-optimization/  # AI optimization
├── settings/         # Settings page
└── profile/          # User profile
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

