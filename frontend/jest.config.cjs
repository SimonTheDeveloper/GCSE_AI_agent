/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/?(*.)+(test|spec).(ts|tsx)'],
  transform: {
    '^.+\\.(ts|tsx)$': 'babel-jest',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  setupFilesAfterEnv: ['<rootDir>/src/test/setupTests.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@radix-ui/(.*)@.*$': '@radix-ui/$1',
    '^class-variance-authority@.*$': 'class-variance-authority',
    '^cmdk@.*$': 'cmdk',
    '^embla-carousel-react@.*$': 'embla-carousel-react',
    '^input-otp@.*$': 'input-otp',
    '^lucide-react@.*$': 'lucide-react',
    '^next-themes@.*$': 'next-themes',
    '^react-day-picker@.*$': 'react-day-picker',
    '^react-hook-form@.*$': 'react-hook-form',
    '^react-resizable-panels@.*$': 'react-resizable-panels',
    '^recharts@.*$': 'recharts',
    '^sonner@.*$': 'sonner',
    '^vaul@.*$': 'vaul',
  },
};
