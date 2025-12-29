import { useState } from 'react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { ChevronDown, User, LogOut, Settings, CreditCard } from 'lucide-react';

interface NavigationProps {
  onLogoClick?: () => void;
  onHomeworkClick?: () => void;
  onLogout?: () => void;
  onSubscriptionClick?: () => void;
}

export function Navigation({ onLogoClick, onHomeworkClick, onLogout, onSubscriptionClick }: NavigationProps) {
  const [activeTab, setActiveTab] = useState('Home');
  const userEmail = localStorage.getItem('userEmail') || 'student@example.com';

  const menuItems = [
    { name: 'Home', hasDropdown: false, onClick: onLogoClick },
    { 
      name: 'Subjects', 
      hasDropdown: true,
      dropdownItems: ['Maths', 'Science', 'English', 'History']
    },
    { name: 'Review', hasDropdown: false },
    { name: 'My Homework', hasDropdown: false, onClick: onHomeworkClick },
  ];

  return (
    <div className="flex items-center justify-between h-16">
      {/* Logo/Brand */}
      <button 
        onClick={onLogoClick}
        className="text-gray-600 hover:text-gray-900 transition-colors"
      >
        GCSE
      </button>

      {/* Navigation Items */}
      <div className="flex items-center gap-8">
        {menuItems.map((item) => (
          <div key={item.name}>
            {item.hasDropdown ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    className={`flex items-center gap-1 pb-4 pt-4 border-b-2 transition-colors ${
                      activeTab === item.name
                        ? 'border-green-500 text-gray-900'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                    onClick={() => setActiveTab(item.name)}
                  >
                    {item.name}
                    <ChevronDown className="h-4 w-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48">
                  {item.dropdownItems?.map((dropdownItem) => (
                    <DropdownMenuItem key={dropdownItem}>
                      {dropdownItem}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <button
                className={`pb-4 pt-4 border-b-2 transition-colors ${
                  activeTab === item.name
                    ? 'border-green-500 text-gray-900'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
                onClick={() => {
                  setActiveTab(item.name);
                  item.onClick?.();
                }}
              >
                {item.name}
              </button>
            )}
          </div>
        ))}
      </div>

      {/* User Menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="gap-2">
            <User className="h-4 w-4" />
            <span className="max-w-[150px] truncate">{userEmail}</span>
            <ChevronDown className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <div className="px-2 py-1.5">
            <p className="text-gray-900">Signed in as</p>
            <p className="text-gray-600 truncate">{userEmail}</p>
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem>
            <User className="h-4 w-4 mr-2" />
            My Profile
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onSubscriptionClick}>
            <CreditCard className="h-4 w-4 mr-2" />
            Subscription
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={onLogout} className="text-red-600">
            <LogOut className="h-4 w-4 mr-2" />
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
