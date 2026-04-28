import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HelpRungs, RungContent } from '../components/views/HelpRungs';

const content: RungContent = {
  nudge: 'Think about what the question is asking.',
  hint: 'Try dividing both sides by 2.',
  workedStep: 'Divide both sides: 2x / 2 = 6 / 2, so x = 3.',
  fullSolution: 'The full worked solution is x = 3 because 2x = 6 means x = 3.',
};

describe('HelpRungs', () => {
  it('shows only Rung 1 (nudge) by default', () => {
    render(<HelpRungs content={content} revealed={1} onReveal={() => {}} />);
    expect(screen.getByText(content.nudge)).toBeInTheDocument();
    expect(screen.queryByText(content.hint)).not.toBeInTheDocument();
    expect(screen.queryByText(content.workedStep)).not.toBeInTheDocument();
    expect(screen.queryByText(content.fullSolution)).not.toBeInTheDocument();
  });

  it('Rung 4 (full solution) is NOT present in the DOM until the user reveals it', () => {
    const { rerender } = render(<HelpRungs content={content} revealed={1} onReveal={() => {}} />);

    // Rung 4 text must be completely absent from the DOM at all intermediate rungs
    expect(screen.queryByText(content.fullSolution)).not.toBeInTheDocument();

    rerender(<HelpRungs content={content} revealed={2} onReveal={() => {}} />);
    expect(screen.queryByText(content.fullSolution)).not.toBeInTheDocument();

    rerender(<HelpRungs content={content} revealed={3} onReveal={() => {}} />);
    expect(screen.queryByText(content.fullSolution)).not.toBeInTheDocument();

    // Only after revealed=4 does the content appear
    rerender(<HelpRungs content={content} revealed={4} onReveal={() => {}} />);
    expect(screen.getByText(content.fullSolution)).toBeInTheDocument();
  });

  it('calls onReveal with the next rung number when the reveal button is clicked', async () => {
    const user = userEvent.setup();
    const onReveal = jest.fn();
    render(<HelpRungs content={content} revealed={1} onReveal={onReveal} />);

    await user.click(screen.getByRole('button', { name: /show hint/i }));
    expect(onReveal).toHaveBeenCalledWith(2);
  });

  it('shows all revealed rungs up to and including the current rung', () => {
    render(<HelpRungs content={content} revealed={3} onReveal={() => {}} />);
    expect(screen.getByText(content.nudge)).toBeInTheDocument();
    expect(screen.getByText(content.hint)).toBeInTheDocument();
    expect(screen.getByText(content.workedStep)).toBeInTheDocument();
    expect(screen.queryByText(content.fullSolution)).not.toBeInTheDocument();
  });

  it('shows no reveal button when all rungs are revealed', () => {
    render(<HelpRungs content={content} revealed={4} onReveal={() => {}} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
