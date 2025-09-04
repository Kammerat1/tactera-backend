import React from 'react';
import { TrendingUpIcon, TrendingDownIcon } from 'lucide-react';
type FinancialSummaryProps = {
  fullView?: boolean;
};
export const FinancialSummary = ({
  fullView = false
}: FinancialSummaryProps) => {
  const finances = {
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
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Finances</h2>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gray-700 p-3 rounded-md">
            <div className="text-xs text-gray-400">Transfer Budget</div>
            <div className="text-lg font-bold mt-1">
              {finances.transferBudget}
            </div>
          </div>
          <div className="bg-gray-700 p-3 rounded-md">
            <div className="text-xs text-gray-400">Wage Budget</div>
            <div className="text-lg font-bold mt-1">{finances.wageBudget}</div>
          </div>
        </div>
        {fullView && <>
            <h3 className="text-sm font-medium text-gray-400 mb-3 mt-5">
              Income
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Matchday</span>
                <span className="text-sm">{finances.income.matchday}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Commercial</span>
                <span className="text-sm">{finances.income.commercial}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Broadcasting</span>
                <span className="text-sm">{finances.income.broadcasting}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Player Sales</span>
                <span className="text-sm">{finances.income.playerSales}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                <span className="text-sm font-medium">Total Income</span>
                <span className="text-sm font-medium text-green-400">
                  {finances.income.total}
                </span>
              </div>
            </div>
            <h3 className="text-sm font-medium text-gray-400 mb-3 mt-5">
              Expenses
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Wages</span>
                <span className="text-sm">{finances.expenses.wages}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Transfers</span>
                <span className="text-sm">{finances.expenses.transfers}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Facilities</span>
                <span className="text-sm">{finances.expenses.facilities}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                <span className="text-sm font-medium">Total Expenses</span>
                <span className="text-sm font-medium text-red-400">
                  {finances.expenses.total}
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