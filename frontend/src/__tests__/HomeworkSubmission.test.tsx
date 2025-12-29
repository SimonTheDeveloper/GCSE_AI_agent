import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HomeworkSubmission } from '../components/HomeworkSubmission';

jest.mock('../lib/api', () => {
  return {
    postHomeworkHelpJson: jest.fn(),
  };
});

import { postHomeworkHelpJson } from '../lib/api';

function mockedPost() {
  return postHomeworkHelpJson as unknown as jest.Mock;
}

describe('HomeworkSubmission', () => {
  it('calls backend and shows processed result', async () => {
    mockedPost().mockResolvedValue({
      result: {
        analysis: { subject: 'Maths', common_mistakes: ['Sign errors'] },
        help: {
          tiers: {
            steps: { content: [{ text: 'Subtract 5 from both sides.' }] },
            hint: { content: [{ text: 'Isolate x.' }] },
            teachback: { content: [{ text: 'We rearrange to solve for x.' }] },
            nudge: { content: [{ text: 'Start by undoing +5.' }] },
            worked: { content: [{ text: '2x+5=17 => 2x=12 => x=6' }] },
          },
        },
      },
    });

    const user = userEvent.setup();

    render(<HomeworkSubmission onViewProblem={() => {}} />);

    const textbox = screen.getByRole('textbox');
    await user.type(textbox, 'Solve for x: 2x + 5 = 17');

    await user.click(screen.getByRole('button', { name: /process with ai/i }));

    await waitFor(() => {
      expect(mockedPost()).toHaveBeenCalledTimes(1);
    });

    expect(mockedPost()).toHaveBeenCalledWith(
      expect.objectContaining({
        text: 'Solve for x: 2x + 5 = 17',
        yearGroup: 9,
        useCache: true,
        uid: expect.any(String),
      })
    );

    // Processed view should appear
    expect(await screen.findByText(/problem processed successfully/i)).toBeInTheDocument();
    // Original submission echoed (can appear in multiple places)
    expect(screen.getAllByText(/solve for x: 2x \+ 5 = 17/i).length).toBeGreaterThan(0);
  });
});
