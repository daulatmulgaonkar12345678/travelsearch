"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navigation from '@/components/layout/Navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiFetch } from '@/lib/api';
import { logoutAdmin } from '@/lib/auth';
import { LogOut, ExternalLink, RefreshCw, MousePointerClick, Plane, Hotel, Bus, Train } from 'lucide-react';

interface Reconciliation {
  click_id: string;
  booking_ref: string;
  provider: string;
  payout: number;
  booked_at: string;
  status: string;
  created_at: string;
}

interface ClickLog {
  service: string;
  vendor: string;
  origin?: string;
  destination?: string;
  city?: string;
  hotel_name?: string;
  price?: number;
  target_url?: string;
  session_id?: string;
  created_at?: string;
  timestamp?: string;
}

interface ClickLogsResponse {
  count: number;
  total: number;
  logs: ClickLog[];
  source?: string;
}

export default function ReconciliationsPage() {
  const [items, setItems] = useState<Reconciliation[]>([]);
  const [clickLogs, setClickLogs] = useState<ClickLog[]>([]);
  const [clickLogsTotal, setClickLogsTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [clickLogsLoading, setClickLogsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clickLogsError, setClickLogsError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    logoutAdmin();
    router.push('/admin/login');
  };

  useEffect(() => {
    setMounted(true);
    fetchReconciliations();
    fetchClickLogs();
  }, []);

  const fetchReconciliations = async () => {
    try {
      setLoading(true);
      const response = await apiFetch('/api/admin/reconciliations');
      if (!response.ok) throw new Error('Failed to fetch reconciliations');
      const data = await response.json();
      setItems(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchClickLogs = async () => {
    try {
      setClickLogsLoading(true);
      const response = await apiFetch('/api/admin/click-logs?limit=100');
      if (!response.ok) throw new Error('Failed to fetch click logs');
      const data: ClickLogsResponse = await response.json();
      setClickLogs(data.logs || []);
      setClickLogsTotal(data.total || 0);
      setClickLogsError(null);
    } catch (err) {
      setClickLogsError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setClickLogsLoading(false);
    }
  };

  const formatDate = (isoString: string | undefined) => {
    if (!isoString || !mounted) return isoString || '-';
    try {
      return new Date(isoString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return isoString;
    }
  };

  const getServiceIcon = (service: string) => {
    switch (service?.toLowerCase()) {
      case 'flight':
      case 'flights':
        return <Plane className="h-4 w-4" />;
      case 'hotel':
      case 'hotels':
        return <Hotel className="h-4 w-4" />;
      case 'bus':
      case 'buses':
        return <Bus className="h-4 w-4" />;
      case 'train':
      case 'trains':
        return <Train className="h-4 w-4" />;
      default:
        return <MousePointerClick className="h-4 w-4" />;
    }
  };

  const getServiceColor = (service: string) => {
    switch (service?.toLowerCase()) {
      case 'flight':
      case 'flights':
        return 'bg-blue-100 text-blue-800';
      case 'hotel':
      case 'hotels':
        return 'bg-purple-100 text-purple-800';
      case 'bus':
      case 'buses':
        return 'bg-orange-100 text-orange-800';
      case 'train':
      case 'trains':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRouteOrLocation = (log: ClickLog) => {
    if (log.origin && log.destination) {
      return `${log.origin} → ${log.destination}`;
    }
    if (log.city) {
      return log.hotel_name ? `${log.hotel_name}, ${log.city}` : log.city;
    }
    if (log.hotel_name) {
      return log.hotel_name;
    }
    return '-';
  };

  const truncateUrl = (url: string | undefined, maxLength: number = 40) => {
    if (!url) return '-';
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength) + '...';
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto p-6 max-w-6xl">
          <Card>
            <CardHeader>
              <CardTitle className="text-3xl">Admin Dashboard</CardTitle>
              <CardDescription>Loading...</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                Loading...
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <div className="container mx-auto p-6 max-w-6xl space-y-6">
        {/* Header with Logout */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <Button 
            variant="outline" 
            onClick={handleLogout}
            className="flex items-center space-x-2"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </Button>
        </div>

        {/* Booking Click Logs Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <MousePointerClick className="h-6 w-6 text-primary" />
                <div>
                  <CardTitle className="text-2xl">Booking Click Logs</CardTitle>
                  <CardDescription>
                    Track all affiliate link clicks across vendors
                  </CardDescription>
                </div>
              </div>
              <Button 
                onClick={fetchClickLogs} 
                variant="outline" 
                size="sm"
                disabled={clickLogsLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${clickLogsLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {clickLogsLoading && (
              <div className="text-center py-8 text-muted-foreground">
                Loading click logs...
              </div>
            )}

            {clickLogsError && (
              <div className="bg-destructive/10 text-destructive p-4 rounded-md">
                Error: {clickLogsError}
              </div>
            )}

            {!clickLogsLoading && !clickLogsError && clickLogs.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <MousePointerClick className="h-12 w-12 mx-auto mb-4 opacity-30" />
                <p className="text-lg">No click logs yet</p>
                <p className="text-sm mt-2">
                  Click events will appear here when users click vendor links
                </p>
              </div>
            )}

            {!clickLogsLoading && !clickLogsError && clickLogs.length > 0 && (
              <div className="space-y-4">
                <div className="flex justify-between items-center mb-4">
                  <p className="text-sm text-muted-foreground">
                    Showing {clickLogs.length} of {clickLogsTotal} total clicks
                  </p>
                </div>

                {/* Click Logs Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3 font-medium">Time</th>
                        <th className="text-left p-3 font-medium">Service</th>
                        <th className="text-left p-3 font-medium">Vendor</th>
                        <th className="text-left p-3 font-medium">Route/Location</th>
                        <th className="text-left p-3 font-medium">Price</th>
                        <th className="text-left p-3 font-medium">Target URL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clickLogs.map((log, idx) => (
                        <tr key={idx} className="border-b hover:bg-muted/30 transition-colors">
                          <td className="p-3 text-muted-foreground whitespace-nowrap">
                            {formatDate(log.created_at || log.timestamp)}
                          </td>
                          <td className="p-3">
                            <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${getServiceColor(log.service)}`}>
                              {getServiceIcon(log.service)}
                              <span className="capitalize">{log.service}</span>
                            </div>
                          </td>
                          <td className="p-3">
                            <Badge variant="outline" className="capitalize">
                              {log.vendor || '-'}
                            </Badge>
                          </td>
                          <td className="p-3 font-medium">
                            {getRouteOrLocation(log)}
                          </td>
                          <td className="p-3">
                            {log.price ? (
                              <span className="text-green-600 font-semibold">
                                ₹{log.price.toLocaleString()}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                          <td className="p-3">
                            {log.target_url ? (
                              <a 
                                href={log.target_url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline"
                                title={log.target_url}
                              >
                                {truncateUrl(log.target_url)}
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Reconciliation Queue Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">Reconciliation Queue</CardTitle>
                <CardDescription>
                  Review pending affiliate bookings and match them with click records
                </CardDescription>
              </div>
              <Button onClick={fetchReconciliations} variant="outline" size="sm">
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Mock Data Notice */}
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                <strong>Note:</strong> This reconciliation section uses sample/mock data. 
                Future work: connect to real affiliate booking webhooks.
              </p>
            </div>

            {loading && (
              <div className="text-center py-8 text-muted-foreground">
                Loading reconciliations...
              </div>
            )}

            {error && (
              <div className="bg-destructive/10 text-destructive p-4 rounded-md">
                Error: {error}
              </div>
            )}

            {!loading && !error && items.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <p className="text-lg">No pending reconciliations</p>
                <p className="text-sm mt-2">
                  New affiliate booking webhooks will appear here
                </p>
              </div>
            )}

            {!loading && !error && items.length > 0 && (
              <div className="space-y-4">
                <div className="flex justify-between items-center mb-4">
                  <p className="text-sm text-muted-foreground">
                    {items.length} pending {items.length === 1 ? 'record' : 'records'}
                  </p>
                </div>

                {items.map((item, idx) => (
                  <Card key={idx} className="bg-muted/30">
                    <CardContent className="pt-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">{item.provider || 'Unknown'}</Badge>
                            <Badge variant="secondary">{item.status}</Badge>
                          </div>
                          <div className="space-y-1 text-sm">
                            <div>
                              <span className="font-semibold">Click ID:</span>{' '}
                              <code className="bg-muted px-1 py-0.5 rounded">
                                {item.click_id}
                              </code>
                            </div>
                            <div>
                              <span className="font-semibold">Booking Ref:</span>{' '}
                              <code className="bg-muted px-1 py-0.5 rounded">
                                {item.booking_ref}
                              </code>
                            </div>
                            <div>
                              <span className="font-semibold">Payout:</span>{' '}
                              <span className="text-green-600 font-semibold">
                                ${item.payout.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-1 text-sm text-muted-foreground">
                          <div>
                            <span className="font-semibold">Booked:</span>{' '}
                            {formatDate(item.booked_at)}
                          </div>
                          <div>
                            <span className="font-semibold">Received:</span>{' '}
                            {formatDate(item.created_at)}
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2 mt-4 pt-4 border-t">
                        <Button size="sm" variant="default" className="bg-green-600 hover:bg-green-700">
                          Mark Settled
                        </Button>
                        <Button size="sm" variant="destructive">
                          Flag Fraud
                        </Button>
                        <Button size="sm" variant="outline">
                          View Click
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
