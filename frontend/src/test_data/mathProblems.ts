// Example math problems for testing/demo purposes

export const mathProblems = [
  {
    id: 1,
    title: 'Linear Equation',
    difficulty: 'Easy' as const,
    category: 'Algebra',
    question: 'Solve for x:\n\n2x + 5 = 17',
    steps: [
      {
        stepNumber: 1,
        prompt: 'Subtract 5 from both sides. What is the result?',
        expectedAnswer: '2x=12',
        hint: 'When you subtract 5 from 17, you get 12. The left side becomes 2x.'
      },
      {
        stepNumber: 2,
        prompt: 'Divide both sides by 2. What is x?',
        expectedAnswer: '6',
        hint: '12 divided by 2 equals 6.'
      },
      {
        stepNumber: 3,
        prompt: 'Verify: Substitute x = 6 into the original equation 2x + 5. What do you get?',
        expectedAnswer: '17',
        hint: '2(6) + 5 = 12 + 5 = 17'
      }
    ],
    explanation: {
      concept: 'To solve a linear equation, we need to isolate the variable (x) by performing inverse operations on both sides of the equation.',
      steps: [
        {
          step: 1,
          title: 'Subtract 5 from both sides',
          content: 'We want to get the term with x by itself. Start by removing the constant term.',
          formula: '2x + 5 - 5 = 17 - 5  →  2x = 12'
        },
        {
          step: 2,
          title: 'Divide both sides by 2',
          content: 'Now divide both sides by the coefficient of x to solve for x.',
          formula: '2x ÷ 2 = 12 ÷ 2  →  x = 6'
        },
        {
          step: 3,
          title: 'Verify your answer',
          content: 'Substitute x = 6 back into the original equation to check.',
          formula: '2(6) + 5 = 12 + 5 = 17 ✓'
        }
      ],
      hint: 'Remember: whatever you do to one side of the equation, you must do to the other side!'
    }
  },
  {
    id: 2,
    title: 'Area of a Circle',
    difficulty: 'Easy' as const,
    category: 'Geometry',
    question: 'Find the area of a circle with radius 5 cm.\n\nUse π ≈ 3.14',
    steps: [
      {
        stepNumber: 1,
        prompt: 'What is the formula for the area of a circle? (Use format: A=πr²)',
        expectedAnswer: 'a=πr²',
        hint: 'The area of a circle uses pi times the radius squared.'
      },
      {
        stepNumber: 2,
        prompt: 'Calculate r² where r = 5. What is 5²?',
        expectedAnswer: '25',
        hint: '5 × 5 = 25'
      },
      {
        stepNumber: 3,
        prompt: 'Multiply 3.14 × 25. What is the area?',
        expectedAnswer: '78.5',
        hint: '3.14 × 25 = 78.5'
      }
    ],
    explanation: {
      concept: 'The area of a circle is calculated using the formula A = πr², where r is the radius.',
      steps: [
        {
          step: 1,
          title: 'Identify the formula',
          content: 'The area formula for a circle uses the radius squared multiplied by π.',
          formula: 'A = πr²'
        },
        {
          step: 2,
          title: 'Calculate r²',
          content: 'First square the radius: r = 5, so r² = 25.',
          formula: '5² = 25'
        },
        {
          step: 3,
          title: 'Calculate the area',
          content: 'Multiply π by r². Using π ≈ 3.14.',
          formula: 'A = 3.14 × 25 = 78.5 cm²'
        }
      ],
      hint: 'Don\'t forget to square the radius before multiplying by π!'
    }
  },{   id: 3,
      title: 'Quadratic Equation',
      difficulty: 'Medium' as const,
      category: 'Algebra',
      question: 'Solve for x using factoring:\n\nx² - 5x + 6 = 0',
      steps: [
        {
          stepNumber: 1,
          prompt: 'Find two numbers that multiply to 6 and add to -5. Enter them as: a,b (smaller first)',
          expectedAnswer: '-3,-2',
          hint: '-3 × -2 = 6 and -3 + -2 = -5'
        },
        {
          stepNumber: 2,
          prompt: 'Factor the equation. Write as: (x+a)(x+b)=0 using your numbers',
          expectedAnswer: '(x-3)(x-2)=0',
          hint: 'Use the numbers from step 1: (x - 3)(x - 2) = 0'
        },
        {
          stepNumber: 3,
          prompt: 'What is the smaller solution for x?',
          expectedAnswer: '2',
          hint: 'Set each factor to zero: x - 3 = 0 or x - 2 = 0'
        }
      ],
      explanation: {
        concept: 'Quadratic equations can be solved by factoring when the expression can be written as a product of two binomials.',
        steps: [
          {
            step: 1,
            title: 'Find the factor numbers',
            content: 'Find two numbers that multiply to 6 and add to -5. These are -3 and -2.',
            formula: '-3 × -2 = 6 and -3 + -2 = -5'
          },
          {
            step: 2,
            title: 'Factor the quadratic',
            content: 'Write the equation as a product of two binomials.',
            formula: 'x² - 5x + 6 = (x - 3)(x - 2) = 0'
          },
          {
            step: 3,
            title: 'Solve for x',
            content: 'Apply the zero product property and solve each factor.',
            formula: 'x - 3 = 0  →  x = 3   OR   x - 2 = 0  →  x = 2'
          }
        ],
        hint: 'When factoring, look for two numbers that multiply to c (6) and add to b (-5).'
      }
    },
    {
      id: 4,
      title: 'Pythagorean Theorem',
      difficulty: 'Medium' as const,
      category: 'Geometry',
      question: 'A right triangle has legs of length 3 cm and 4 cm.\n\nFind the length of the hypotenuse.',
      steps: [
        {
          stepNumber: 1,
          prompt: 'Write the Pythagorean theorem formula (use format: a²+b²=c²)',
          expectedAnswer: 'a²+b²=c²',
          hint: 'The sum of the squares of the legs equals the square of the hypotenuse.'
        },
        {
          stepNumber: 2,
          prompt: 'Calculate 3² + 4². What is the result?',
          expectedAnswer: '25',
          hint: '3² = 9 and 4² = 16, so 9 + 16 = 25'
        },
        {
          stepNumber: 3,
          prompt: 'Take the square root of your answer. What is c?',
          expectedAnswer: '5',
          hint: '√25 = 5'
        }
      ],
      explanation: {
        concept: 'The Pythagorean theorem states that in a right triangle, the square of the hypotenuse equals the sum of squares of the other two sides.',
        steps: [
          {
            step: 1,
            title: 'Write the formula',
            content: 'For a right triangle with legs a and b, and hypotenuse c.',
            formula: 'a² + b² = c²'
          },
          {
            step: 2,
            title: 'Substitute and calculate',
            content: 'Here, a = 3 and b = 4. Calculate the sum of their squares.',
            formula: '3² + 4² = 9 + 16 = 25 = c²'
          },
          {
            step: 3,
            title: 'Solve for c',
            content: 'Take the square root of both sides.',
            formula: 'c = √25 = 5'
          }
        ],
        hint: 'The hypotenuse is always the longest side, opposite the right angle.'
      }
    },
    {
      id: 5,
      title: 'System of Equations',
      difficulty: 'Hard' as const,
      category: 'Algebra',
      question: 'Solve the system:\n\n2x + y = 10\nx - y = 2',
      steps: [
        {
          stepNumber: 1,
          prompt: 'Add the two equations together. What equation do you get? (format: 3x=12)',
          expectedAnswer: '3x=12',
          hint: '(2x + y) + (x - y) = 10 + 2, the y terms cancel out'
        },
        {
          stepNumber: 2,
          prompt: 'Solve for x. What is x?',
          expectedAnswer: '4',
          hint: 'Divide both sides of 3x = 12 by 3'
        },
        {
          stepNumber: 3,
          prompt: 'Substitute x = 4 into the second equation (x - y = 2). What is y?',
          expectedAnswer: '2',
          hint: '4 - y = 2, so y = 2'
        },
        {
          stepNumber: 4,
          prompt: 'Verify: Calculate 2x + y using x = 4 and y = 2',
          expectedAnswer: '10',
          hint: '2(4) + 2 = 8 + 2 = 10 ✓'
        }
      ],
      explanation: {
        concept: 'Systems of equations can be solved using elimination or substitution. Here we\'ll use elimination.',
        steps: [
          {
            step: 1,
            title: 'Add the equations',
            content: 'Notice that y and -y will cancel when we add the equations.',
            formula: '(2x + y) + (x - y) = 10 + 2  →  3x = 12'
          },
          {
            step: 2,
            title: 'Solve for x',
            content: 'Divide both sides by 3.',
            formula: '3x ÷ 3 = 12 ÷ 3  →  x = 4'
          },
          {
            step: 3,
            title: 'Find y',
            content: 'Substitute x = 4 into the second equation.',
            formula: '4 - y = 2  →  y = 2'
          },
          {
            step: 4,
            title: 'Verification',
            content: 'Check the solution in the first equation.',
            formula: '2(4) + 2 = 8 + 2 = 10 ✓'
          }
        ],
        hint: 'Look for a way to eliminate one variable by adding or subtracting the equations.'
      }
    }
  ];

