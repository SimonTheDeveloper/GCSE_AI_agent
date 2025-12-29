# View Components

This directory contains presentational (view) components that are separated from business logic.

## Architecture Pattern

The components follow a **View-Logic separation pattern**:

- **View Components** (in `/components/views/`): Pure presentational components that receive all data and handlers via props. They focus solely on rendering UI.
- **Logic Components** (in `/components/`): Container components that manage state, side effects, and business logic, then pass data to view components.

## Benefits

1. **Reusability**: View components can be easily imported and used in different contexts
2. **Testability**: Logic and presentation can be tested independently
3. **Maintainability**: Clear separation of concerns makes code easier to understand and modify
4. **Integration**: Easier to integrate into existing applications by providing custom logic

## Available View Components

### LoginView
**File**: `LoginView.tsx`  
**Props**: `LoginViewProps`  
**Purpose**: Login form with email/password fields, remember me, and demo account option

**Example Usage**:
```tsx
import { LoginView } from './components/views/LoginView';

<LoginView
  email={email}
  password={password}
  rememberMe={rememberMe}
  error={error}
  isLoading={isLoading}
  onEmailChange={setEmail}
  onPasswordChange={setPassword}
  onRememberMeChange={setRememberMe}
  onSubmit={handleSubmit}
  onDemoLogin={handleDemoLogin}
  onSignUpClick={handleSignUpClick}
/>
```

### SignUpView
**File**: `SignUpView.tsx`  
**Props**: `SignUpViewProps`  
**Purpose**: Registration form with full name, email, password, grade level, and terms acceptance

**Example Usage**:
```tsx
import { SignUpView } from './components/views/SignUpView';

<SignUpView
  formData={formData}
  acceptTerms={acceptTerms}
  error={error}
  isLoading={isLoading}
  passwordStrength={passwordStrength}
  onFormDataChange={handleInputChange}
  onAcceptTermsChange={setAcceptTerms}
  onSubmit={handleSubmit}
  onLoginClick={handleLoginClick}
/>
```

### MathProblemView
**File**: `MathProblemView.tsx`  
**Props**: `MathProblemViewProps`  
**Purpose**: Interactive step-by-step math problem solver with progress tracking

**Example Usage**:
```tsx
import { MathProblemView } from './components/views/MathProblemView';

<MathProblemView
  problem={problem}
  currentStepIndex={currentStepIndex}
  stepAnswers={stepAnswers}
  stepFeedback={stepFeedback}
  showHint={showHint}
  attempts={attempts}
  progress={progress}
  completedSteps={completedSteps}
  allStepsComplete={allStepsComplete}
  onStepAnswerChange={updateStepAnswer}
  onCheckAnswer={checkStepAnswer}
  onGoToStep={goToStep}
  onToggleHint={() => setShowHint(!showHint)}
  onReset={resetProblem}
  onKeyDown={handleKeyDown}
/>
```

### HomeworkSubmissionView
**File**: `HomeworkSubmissionView.tsx`  
**Props**: `HomeworkSubmissionViewProps`  
**Purpose**: Multi-tab homework submission interface (type, upload, paste)

**Example Usage**:
```tsx
import { HomeworkSubmissionView } from './components/views/HomeworkSubmissionView';

<HomeworkSubmissionView
  textInput={textInput}
  uploadedFiles={uploadedFiles}
  pastedImage={pastedImage}
  activeTab={activeTab}
  isProcessing={isProcessing}
  processingProgress={processingProgress}
  isDragging={isDragging}
  canSubmit={canSubmit}
  onTextInputChange={setTextInput}
  onFileUpload={handleFileUpload}
  onPaste={handlePaste}
  onDragOver={handleDragOver}
  onDragLeave={handleDragLeave}
  onDrop={handleDrop}
  onRemoveFile={removeFile}
  onRemovePastedImage={() => setPastedImage(null)}
  onActiveTabChange={setActiveTab}
  onProcess={processHomework}
  onFileInputClick={() => fileInputRef.current?.click()}
  fileInputRef={fileInputRef}
/>
```

### ProcessedResultView
**File**: `HomeworkSubmissionView.tsx`  
**Props**: `ProcessedResultViewProps`  
**Purpose**: Displays processed homework with original submission and interactive preview

**Example Usage**:
```tsx
import { ProcessedResultView } from './components/views/HomeworkSubmissionView';

<ProcessedResultView
  textInput={textInput}
  uploadedFiles={uploadedFiles}
  pastedImage={pastedImage}
  onSubmitAnother={handleSubmitAnother}
  onViewProblem={onViewProblem}
  problemPreview={<MathProblem {...problemProps} />}
/>
```

## Integration Guide

### Using View Components in Your Application

1. **Import the view component**:
   ```tsx
   import { LoginView } from './components/views/LoginView';
   ```

2. **Create your own logic/state management**:
   ```tsx
   const [email, setEmail] = useState('');
   const [password, setPassword] = useState('');
   // ... other state
   ```

3. **Implement your handlers**:
   ```tsx
   const handleSubmit = async (e: React.FormEvent) => {
     e.preventDefault();
     // Your custom authentication logic
     await yourAuthService.login(email, password);
   };
   ```

4. **Render the view component**:
   ```tsx
   return (
     <LoginView
       email={email}
       password={password}
       // ... pass all required props
       onSubmit={handleSubmit}
     />
   );
   ```

### Using Logic Components (Default)

If you prefer to use the pre-built logic, just import the regular component:

```tsx
import { Login } from './components/Login';

<Login 
  onLoginSuccess={() => console.log('Logged in!')}
  onSignUpClick={() => setView('signup')}
/>
```

## Type Safety

All view components export their props as TypeScript interfaces (e.g., `LoginViewProps`, `SignUpViewProps`). Import these for type-safe integration:

```tsx
import { LoginView, type LoginViewProps } from './components/views/LoginView';
```

## Notes

- View components are **stateless** - all state must be passed via props
- View components should **not** import or use hooks like `useState`, `useEffect`
- All event handlers are passed as props with clear naming (e.g., `onEmailChange`, `onSubmit`)
- Error handling and validation should be done in the logic layer
