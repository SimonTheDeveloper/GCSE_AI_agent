import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Alert, AlertDescription } from '../ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { BookOpen, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';

export interface SignUpViewProps {
  formData: {
    fullName: string;
    email: string;
    password: string;
    confirmPassword: string;
    gradeLevel: string;
  };
  acceptTerms: boolean;
  error: string;
  isLoading: boolean;
  passwordStrength: 'weak' | 'medium' | 'strong' | null;
  onFormDataChange: (field: string, value: string) => void;
  onAcceptTermsChange: (checked: boolean) => void;
  onSubmit: (e: React.FormEvent) => void;
  onLoginClick: () => void;
  onTermsClick?: () => void;
  onPrivacyClick?: () => void;
}

export function SignUpView({
  formData,
  acceptTerms,
  error,
  isLoading,
  passwordStrength,
  onFormDataChange,
  onAcceptTermsChange,
  onSubmit,
  onLoginClick,
  onTermsClick,
  onPrivacyClick
}: SignUpViewProps) {
  const getPasswordStrengthColor = () => {
    if (!passwordStrength) return '';
    switch (passwordStrength) {
      case 'weak':
        return 'bg-red-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'strong':
        return 'bg-green-500';
    }
  };

  const getPasswordStrengthText = () => {
    if (!passwordStrength) return '';
    switch (passwordStrength) {
      case 'weak':
        return 'Weak password';
      case 'medium':
        return 'Medium strength';
      case 'strong':
        return 'Strong password';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo and Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <BookOpen className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-gray-900 mb-2">GCSE Math Tutor</h1>
          <p className="text-gray-600">Create your account to start learning</p>
        </div>

        {/* Sign Up Card */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Create an account</CardTitle>
            <CardDescription>
              Join thousands of students mastering GCSE maths
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="John Smith"
                  value={formData.fullName}
                  onChange={(e) => onFormDataChange('fullName', e.target.value)}
                  required
                  disabled={isLoading}
                  className="bg-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your.email@example.com"
                  value={formData.email}
                  onChange={(e) => onFormDataChange('email', e.target.value)}
                  required
                  disabled={isLoading}
                  className="bg-white"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="gradeLevel">Grade Level</Label>
                <Select
                  value={formData.gradeLevel}
                  onValueChange={(value) => onFormDataChange('gradeLevel', value)}
                  disabled={isLoading}
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Select your year" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="year7">Year 7</SelectItem>
                    <SelectItem value="year8">Year 8</SelectItem>
                    <SelectItem value="year9">Year 9</SelectItem>
                    <SelectItem value="year10">Year 10 (GCSE)</SelectItem>
                    <SelectItem value="year11">Year 11 (GCSE)</SelectItem>
                    <SelectItem value="year12">Year 12 (A-Level)</SelectItem>
                    <SelectItem value="year13">Year 13 (A-Level)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Create a strong password"
                  value={formData.password}
                  onChange={(e) => onFormDataChange('password', e.target.value)}
                  required
                  minLength={6}
                  disabled={isLoading}
                  className="bg-white"
                />
                {passwordStrength && (
                  <div className="space-y-1">
                    <div className="flex gap-1">
                      <div className={`h-1 flex-1 rounded ${passwordStrength === 'weak' ? getPasswordStrengthColor() : 'bg-gray-200'}`} />
                      <div className={`h-1 flex-1 rounded ${passwordStrength === 'medium' || passwordStrength === 'strong' ? getPasswordStrengthColor() : 'bg-gray-200'}`} />
                      <div className={`h-1 flex-1 rounded ${passwordStrength === 'strong' ? getPasswordStrengthColor() : 'bg-gray-200'}`} />
                    </div>
                    <p className={`text-xs ${passwordStrength === 'weak' ? 'text-red-600' : passwordStrength === 'medium' ? 'text-yellow-600' : 'text-green-600'}`}>
                      {getPasswordStrengthText()}
                    </p>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Re-enter your password"
                  value={formData.confirmPassword}
                  onChange={(e) => onFormDataChange('confirmPassword', e.target.value)}
                  required
                  disabled={isLoading}
                  className="bg-white"
                />
                {formData.confirmPassword && formData.password === formData.confirmPassword && (
                  <p className="text-xs text-green-600 flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Passwords match
                  </p>
                )}
              </div>

              <div className="flex items-start space-x-2">
                <Checkbox
                  id="terms"
                  checked={acceptTerms}
                  onCheckedChange={(checked) => onAcceptTermsChange(checked as boolean)}
                  disabled={isLoading}
                />
                <label
                  htmlFor="terms"
                  className="text-gray-700 cursor-pointer select-none leading-snug"
                >
                  I agree to the{' '}
                  <button
                    type="button"
                    className="text-blue-600 hover:text-blue-700"
                    onClick={onTermsClick || (() => alert('Terms of Service would be displayed here'))}
                  >
                    Terms of Service
                  </button>
                  {' '}and{' '}
                  <button
                    type="button"
                    className="text-blue-600 hover:text-blue-700"
                    onClick={onPrivacyClick || (() => alert('Privacy Policy would be displayed here'))}
                  >
                    Privacy Policy
                  </button>
                </label>
              </div>

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </Button>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <div className="text-center text-gray-600 w-full">
              Already have an account?{' '}
              <button
                type="button"
                className="text-blue-600 hover:text-blue-700 transition-colors"
                onClick={onLoginClick}
                disabled={isLoading}
              >
                Sign in
              </button>
            </div>
          </CardFooter>
        </Card>

        {/* Additional Info */}
        <div className="mt-6 text-center text-gray-500">
          <p className="mb-2">Free for all students • No credit card required</p>
        </div>
      </div>
    </div>
  );
}
