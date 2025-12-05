"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Reconciliation {
  click_id: string;
  booking_ref: string;
  provider: string;
  payout: number;
  booked_at: string;
  status: string;
  created_at: string;
}

export default function ReconciliationsPage() {
  const [items, setItems] = useState<Reconciliation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchReconciliations();
  }, []);

  const fetchReconciliations = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/api/admin/reconciliations`);
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

  const formatDate = (isoString: string) => {
    if (!mounted) return isoString;
    return new Date(isoString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  if (!mounted) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-3xl">Reconciliation Queue</CardTitle>
            <CardDescription>
              Review pending affiliate bookings and match them with click records
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              Loading...
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">Reconciliation Queue</CardTitle>
          <CardDescription>
            Review pending affiliate bookings and match them with click records
          </CardDescription>
        </CardHeader>
        <CardContent>
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
                <Button onClick={fetchReconciliations} variant="outline" size="sm">
                  Refresh
                </Button>
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
  );
}
