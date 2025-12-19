"use client"

import Link from 'next/link'
import { Plane } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()
  
  const legalLinks = [
    { href: '/privacy-policy', label: 'Privacy Policy' },
    { href: '/terms-and-conditions', label: 'Terms & Conditions' },
    { href: '/disclaimer', label: 'Disclaimer' },
  ]
  
  const companyLinks = [
    { href: '/about', label: 'About Us' },
    { href: '/contact', label: 'Contact' },
  ]
  
  return (
    <footer className="bg-gray-50 border-t mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center space-x-2 mb-4">
              <Plane className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-display font-bold text-gray-900">TravelSearch</span>
            </Link>
            <p className="text-sm text-gray-600">
              Compare flights and hotels from multiple providers. Find the best travel deals instantly.
            </p>
          </div>
          
          {/* Legal Links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Legal</h3>
            <ul className="space-y-2">
              {legalLinks.map((link) => (
                <li key={link.href}>
                  <Link 
                    href={link.href}
                    className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Company Links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Company</h3>
            <ul className="space-y-2">
              {companyLinks.map((link) => (
                <li key={link.href}>
                  <Link 
                    href={link.href}
                    className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        {/* Bottom Bar */}
        <div className="mt-8 pt-6 border-t text-center text-sm text-gray-600">
          <p>&copy; {currentYear} TravelSearch. All rights reserved.</p>
          <p className="mt-2 text-xs">
            Travel meta-search platform. Prices and availability provided by third-party suppliers.
          </p>
        </div>
      </div>
    </footer>
  )
}
