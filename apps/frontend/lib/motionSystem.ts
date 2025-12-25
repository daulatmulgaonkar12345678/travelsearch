/**
 * Phase 2 Motion System
 * Consistent, accessible animations for trust & conversion elements
 */

/**
 * Animation variants for Framer Motion or CSS classes
 */
export const motionConfig = {
  // Durations
  duration: {
    instant: 120,
    fast: 200,
    normal: 250,
    slow: 300,
  },
  
  // Easing curves
  easing: {
    out: 'cubic-bezier(0.16, 1, 0.3, 1)',
    standard: 'ease-out',
  },
  
  // Standard fade in
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] }
  },
  
  // Fade in with slide up
  fadeInUp: {
    initial: { opacity: 0, y: 6 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] }
  },
  
  // Scale in (for modals)
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] }
  },
  
  // Micro-interaction (buttons)
  microPress: {
    whileTap: { scale: 0.98 },
    transition: { duration: 0.12 }
  },
  
  // Staggered children
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.07
      }
    }
  },
  
  staggerItem: {
    initial: { opacity: 0, y: 4 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] }
  }
}

/**
 * CSS Animation Classes (for non-Framer components)
 */
export const animationClasses = {
  fadeIn: 'animate-[fadeIn_0.3s_ease-out]',
  fadeInUp: 'animate-[fadeInUp_0.25s_ease-out]',
  scaleIn: 'animate-[scaleIn_0.2s_ease-out]',
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Conditionally apply animation based on user preference
 */
export function withMotion<T>(animation: T, fallback: T = {} as T): T {
  return prefersReducedMotion() ? fallback : animation
}

/**
 * Stagger delay helper
 */
export function getStaggerDelay(index: number, baseDelay: number = 70): number {
  return index * baseDelay
}
