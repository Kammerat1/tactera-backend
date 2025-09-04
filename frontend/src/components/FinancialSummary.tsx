import React, { useState, useEffect } from 'react';
import { TrendingUpIcon, TrendingDownIcon } from 'lucide-react';
import { api } from '../services/api';
type FinancialSummaryProps = {
  fullView?: boolean;
};
export const FinancialSummary = ({
  fullView = false
}: FinancialSummaryProps) => {
  const [finances, setFinances] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // For now, assuming manager is associated with club ID 1
  // TODO: Get actual club ID from user context
  const clubId = 1;

  useEffect(() => {
    const fetchFinances = async () => {
      try {
        setLoading(true);
        const data = await api.stadium.getFinancialSummary(clubId);
        setFinances(data);
      } catch (err) {
        console.error('Failed to fetch financial data:', err);
        setError('Failed to load financial data');
      } finally {
        setLoading(false);
      }
    };

    fetchFinances();
  }, [clubId]);

  // Loading state
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-md p-6">
        <div className="text-center text-gray-400">Loading finances...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-md p-6">
        <div className="text-center text-red-400">{error}</div>
      </div>
    );
  }

  // If no data, show fallback
  if (!finances) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-md p-6">
        <div className="text-center text-gray-400">No financial data available</div>
      </div>
    );
  }

  // Format currency values
  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `€${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `€${(amount / 1000).toFixed(0)}K`;
    } else {
      return `€${amount}`;
    }
  };

  const mockFinances = {
    balance: '€65.4M',
    transferBudget: '€42.8M',
    wageBudget: '€3.2M/week',
    income: {
      total: '€124.5M',
      matchday: '€42.3M',
      commercial: '€35.7M',
      broadcasting: '€38.2M',
      playerSales: '€8.3M'
    },
    expenses: {
      total: '€89.1M',
      wages: '€65.4M',
      transfers: '€18.3M',
      facilities: '€5.4M'
    }
  };
  
  // Use real data from backend
  const currentMoney = finances.club_info?.current_money || 0;
  const perMatchRevenue = finances.current_revenue?.per_match || 0;
  const stadiumCapacity = finances.stadium_info?.current_capacity || 0;
  const ticketPrice = finances.stadium_info?.ticket_price || 0;
  
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden card-hover-subtle">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold">{finances.club_info?.name || 'Club'} Finances</h2>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gray-700 p-3 rounded-md">
            <div className="text-xs text-gray-400">Current Money</div>
            <div className="text-lg font-bold mt-1 text-green-400">
              {formatCurrency(currentMoney)}
            </div>
          </div>
          <div className="bg-gray-700 p-3 rounded-md">
            <div className="text-xs text-gray-400">Match Revenue</div>
            <div className="text-lg font-bold mt-1 text-blue-400">
              {formatCurrency(perMatchRevenue)}
            </div>
          </div>
        </div>
        {fullView && <>
            <h3 className="text-sm font-medium text-gray-400 mb-3 mt-5">
              Stadium Information
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Stadium Name</span>
                <span className="text-sm font-semibold">{finances.stadium_info?.name || 'Unknown Stadium'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Stadium Capacity</span>
                <span className="text-sm font-semibold">{stadiumCapacity.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Ticket Price</span>
                <span className="text-sm font-semibold">€{ticketPrice}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Pitch Quality</span>
                <span className="text-sm font-semibold">{finances.stadium_info?.current_pitch_quality || 0}%</span>
              </div>
            </div>
            
            <h3 className="text-sm font-medium text-gray-400 mb-3 mt-5">
              Revenue Breakdown
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">50% Attendance</span>
                <span className="text-sm font-semibold">{formatCurrency(finances.current_revenue?.attendance_breakdown?.['50%_attendance'] || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">80% Attendance</span>
                <span className="text-sm font-semibold text-blue-400">{formatCurrency(finances.current_revenue?.attendance_breakdown?.['80%_attendance'] || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Sold Out</span>
                <span className="text-sm font-semibold text-green-400">{formatCurrency(finances.current_revenue?.attendance_breakdown?.['100%_sold_out'] || 0)}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                <span className="text-sm font-medium">Per Season (80% avg)</span>
                <span className="text-sm font-medium text-green-400">
                  {formatCurrency(finances.current_revenue?.per_season || 0)}
                </span>
              </div>
            </div>
            
            <h3 className="text-sm font-medium text-gray-400 mb-3 mt-5">
              Upgrade Potential
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Max Capacity (After Upgrades)</span>
                <span className="text-sm font-semibold">{finances.upgrade_potential?.max_capacity_after_upgrades?.toLocaleString() || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Potential Revenue/Match</span>
                <span className="text-sm font-semibold text-green-400">{formatCurrency(finances.upgrade_potential?.potential_revenue_per_match || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Estimated Upgrade Cost</span>
                <span className="text-sm font-semibold text-red-400">{formatCurrency(finances.upgrade_potential?.estimated_upgrade_cost || 0)}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                <span className="text-sm font-medium">Revenue Increase/Match</span>
                <span className="text-sm font-medium text-green-400">
                  +{formatCurrency(finances.upgrade_potential?.revenue_increase_per_match || 0)}
                </span>
              </div>
            </div>
          </>}
        <div className={`flex justify-between items-center ${fullView ? 'pt-4 mt-4 border-t border-gray-700' : 'mt-2'}`}>
          <span className={fullView ? 'text-base font-medium' : 'text-sm'}>
            Current Balance
          </span>
          <div className="flex items-center">
            <span className={`font-bold ${fullView ? 'text-lg' : 'text-base'}`}>
              {finances.balance}
            </span>
            <TrendingUpIcon size={16} className="ml-1 text-green-400" />
          </div>
        </div>
      </div>
    </div>;
};