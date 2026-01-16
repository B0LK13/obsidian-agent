# Usage Examples

This document provides real-world examples of how to use Obsidian Agent.

## Example 1: Meeting Notes to Action Items

**Before:**
```markdown
Met with Sarah and John about Q1 planning
- Need to finalize budget
- Review team structure  
- Set milestones
```

**Command:** Select text → "Expand Ideas"

**After:**
```markdown
# Q1 Planning Meeting Summary

## Attendees
- Sarah (Project Manager)
- John (Team Lead)
- Myself

## Key Discussion Points

### Budget Finalization
We discussed the need to finalize the Q1 budget before the end of this month. This includes:
- Reviewing current spending patterns
- Allocating resources for new initiatives
- Getting approval from finance department

### Team Structure Review
The current team structure needs evaluation to ensure we have:
- Proper role distribution
- Adequate coverage for all project areas
- Clear reporting lines and responsibilities

### Milestone Setting
We need to establish clear Q1 milestones including:
- Weekly sprint goals
- Monthly deliverables
- End-of-quarter targets
```

## Example 2: Research Paper Summary

**Before:** Long research paper content

**Command:** "Generate Summary"

**After:**
```markdown
## Summary
This research paper explores the effectiveness of AI-assisted learning in higher education.
The study found that students using AI tools showed 23% improvement in comprehension and
35% reduction in time spent on research tasks. However, the authors caution that over-reliance
on AI may reduce critical thinking skills if not properly integrated into curricula.
```

## Example 3: Blog Post Improvement

**Before:**
```markdown
AI is really cool and helpful. It can do lots of things like writing and coding.
Many people use it now. Its getting more popular everyday.
```

**Command:** Select text → "Improve Writing"

**After:**
```markdown
Artificial Intelligence has emerged as a transformative technology with diverse applications
in writing, coding, and creative tasks. The adoption rate continues to accelerate as
individuals and organizations discover its potential to enhance productivity and innovation.
Its growing accessibility has made it an invaluable tool across various industries.
```

## Example 4: Project Planning

**Before:**
```markdown
Build a personal website
```

**Command:** Select "Build a personal website" → "Generate Outline"

**After:**
```markdown
# Personal Website Project Outline

## 1. Planning Phase
   - Define website purpose and goals
   - Identify target audience
   - Create content strategy
   - Determine required features

## 2. Design Phase
   - Sketch wireframes
   - Choose color scheme and typography
   - Design responsive layouts
   - Create style guide

## 3. Development Phase
   - Set up development environment
   - Choose tech stack (HTML/CSS/JS framework)
   - Build homepage
   - Create additional pages
   - Implement responsive design
   - Add interactive features

## 4. Content Creation
   - Write about page
   - Develop portfolio/project showcase
   - Create blog section
   - Prepare contact information

## 5. Testing
   - Cross-browser compatibility
   - Mobile responsiveness
   - Load time optimization
   - Accessibility compliance

## 6. Deployment
   - Choose hosting provider
   - Set up domain name
   - Deploy website
   - Configure SSL certificate

## 7. Maintenance
   - Regular content updates
   - Security patches
   - Performance monitoring
   - SEO optimization
```

## Example 5: Learning Notes Enhancement

**Command:** "Ask AI Agent"

**Prompt in modal:** "Explain this concept in simpler terms with an example"

**Result:**
```markdown
The Pomodoro Technique is a time management method where you work in focused
25-minute intervals (called "pomodoros"), followed by 5-minute breaks. After
four pomodoros, you take a longer 15-30 minute break.

**Example:**
- 9:00-9:25: Write report (Pomodoro 1)
- 9:25-9:30: Quick break
- 9:30-9:55: Continue report (Pomodoro 2)
- 9:55-10:00: Quick break
- 10:00-10:25: Edit report (Pomodoro 3)
- 10:25-10:30: Quick break
- 10:30-10:55: Finalize report (Pomodoro 4)
- 10:55-11:25: Long break
```

## Example 6: Question Answering

**Note contains:**
```markdown
# JavaScript Closures

A closure is a function that has access to variables in its outer scope,
even after the outer function has returned. This is possible because
functions in JavaScript form closures around the data they need to access.

function outer() {
  let count = 0;
  return function inner() {
    count++;
    return count;
  }
}
```

**Command:** "Answer Question Based on Note"

**Prompt:** "What's a practical use case for closures?"

**Result:**
```markdown
**Q:** What's a practical use case for closures?

**A:** Closures are commonly used for data encapsulation and creating private variables.
A practical example is creating a counter function where you want to maintain state
without exposing the counter variable globally. The closure allows the inner function
to access and modify the `count` variable, but external code cannot directly access
or modify it, providing a form of data privacy. This pattern is useful for:

- Creating factory functions
- Implementing module patterns  
- Event handlers that need to remember state
- Callbacks that need access to outer scope variables
```

## Example 7: Creative Writing

**Before:**
```markdown
Story idea: A detective who can see emotions as colors
```

**Command:** Select text → "Expand Ideas"

**After:**
```markdown
# Story Concept: The Chromatic Detective

## Premise
In a neo-noir cityscape, Detective Morgan Chen possesses an unusual gift: the ability
to perceive human emotions as visible auras of color. While this synesthetic ability
makes her an exceptional interrogator, it comes with a heavy price—she can never
truly escape the emotional turbulence of those around her.

## Character Development
- **Protagonist**: Morgan Chen, 34, jaded but determined
- **Gift**: Sees fear as purple shadows, anger as crimson halos, guilt as sickly green mist
- **Conflict**: Her ability attracts both criminals who fear exposure and agencies who
  want to weaponize her gift

## Plot Points
1. A murder with no emotional residue—suggesting a psychopath or something more sinister
2. Morgan must navigate a web of colorful lies to find a killer who has no emotional signature
3. Questions about the nature of humanity and what makes us truly conscious

## Themes
- The burden of empathy
- Privacy vs. truth
- What defines humanity—emotions or actions?
```

## Tips for Better Results

1. **Be Specific**: "Expand this into a professional email" works better than just "expand"
2. **Provide Context**: The more context in your note, the better the AI understands your needs
3. **Iterate**: Use multiple commands in sequence to refine output
4. **Customize System Prompt**: Adjust the AI's personality in settings for consistent style
5. **Experiment**: Try different commands for different tasks to see what works best

## Advanced Workflows

### Research → Summary → Questions
1. Paste research material
2. Generate summary
3. Ask questions about unclear points

### Brainstorm → Outline → Expand
1. Quick brainstorm ideas
2. Generate outline
3. Expand each section

### Draft → Improve → Review
1. Write rough draft
2. Improve writing quality
3. Ask AI to review for issues
