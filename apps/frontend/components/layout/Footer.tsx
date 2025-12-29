"use client"

import Link from 'next/link'
import { Plane, Shield } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()
  
  const legalLinks = [
    { href: '/privacy-policy', label: 'Privacy Policy' },
    { href: '/terms-and-conditions', label: 'Terms & Conditions' },
    { href: '/service-disclaimer', label: 'Disclaimer' },
    { href: '/affiliate-disclosure', label: 'Affiliate Disclosure' },
  ]
  
  const companyLinks = [
    { href: '/about-us', label: 'About Us' },
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
            <p className="text-sm text-gray-600 mb-3">
              Compare flights, trains, buses, and hotels from verified travel partners. Find the best deals instantly.
            </p>
            {/* Trust Badge */}
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Shield className="h-4 w-4 text-green-600" />
              <span>Secure bookings on partner websites</span>
            </div>
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
        
        {/* Trust Statement + Copyright */}
        <div className="mt-8 pt-6 border-t">
          {/* Trust Statement */}
          <p className="text-center text-sm text-gray-600 mb-3">
            TravelSearch is a travel meta-search platform. Bookings are completed securely on partner websites.
          </p>
          {/* Copyright */}
          <p className="text-center text-xs text-gray-500">
            &copy; {currentYear} TravelSearch. All rights reserved. Prices and availability provided by third-party suppliers.
          </p>
        </div>
      </div>
    </footer>
  )
}
