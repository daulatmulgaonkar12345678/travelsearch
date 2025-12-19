"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Plane, Hotel } from 'lucide-react'

export default function Navigation() {
  const pathname = usePathname()
  
  const navItems = [
    { href: '/', label: 'Flights', icon: Plane },
    { href: '/hotels', label: 'Hotels', icon: Hotel },
  ]
  
  return (
    <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <Plane className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-display font-bold text-gray-900">TravelSearch</h1>
          </Link>
          
          <nav className="flex items-center space-x-1 md:space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href || 
                              (item.href !== '/' && pathname.startsWith(item.href))
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center space-x-2 px-3 md:px-4 py-2 rounded-lg
                    transition-all duration-200 font-medium text-sm md:text-base
                    ${isActive 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
