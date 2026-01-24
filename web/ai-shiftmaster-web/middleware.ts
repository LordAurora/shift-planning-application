import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Protected routes that require authentication
 */
const PROTECTED_ROUTES = [
  '/dashboard',
  '/shifts',
  '/employees',
  '/rules',
  '/settings',
  '/ai-optimization',
  '/profile',
  '/security',
];

/**
 * Public routes that don't require authentication
 */
const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
];

/**
 * Admin-only routes
 */
const ADMIN_ROUTES = [
  '/employees',
  '/rules',
  '/settings/system',
  '/security/rules',
  '/security/training',
  '/security/migration',
];

/**
 * Manager and above routes
 */
const MANAGER_ROUTES = [
  '/ai-optimization',
  '/shifts/manage',
];

/**
 * Next.js middleware for authentication and authorization
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Skip middleware for static files and API routes
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') // Static files
  ) {
    return NextResponse.next();
  }

  // Get token from cookie
  const token = request.cookies.get('auth_token')?.value;
  const userRole = request.cookies.get('user_role')?.value;

  // Check if route is protected
  const isProtectedRoute = PROTECTED_ROUTES.some(route => 
    pathname.startsWith(route)
  );
  
  // Check if route is public
  const isPublicRoute = PUBLIC_ROUTES.some(route => 
    pathname.startsWith(route)
  );

  // If accessing protected route without token, redirect to login
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // If authenticated user tries to access login page, redirect to dashboard
  if (isPublicRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Role-based access control
  if (token && userRole) {
    // Check admin routes
    const isAdminRoute = ADMIN_ROUTES.some(route => 
      pathname.startsWith(route)
    );
    
    if (isAdminRoute && userRole !== 'admin' && userRole !== 'super_admin') {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    // Check manager routes
    const isManagerRoute = MANAGER_ROUTES.some(route => 
      pathname.startsWith(route)
    );
    
    if (isManagerRoute && !['admin', 'super_admin', 'manager'].includes(userRole)) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  // Add security headers
  const response = NextResponse.next();
  
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=()'
  );

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
