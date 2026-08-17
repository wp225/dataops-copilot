# Candidate Setup

Run `/setup` before using job ranking or application workflows.

## First-time setup

1. Add one CV to `documents/original_resume/`, or paste its text into the conversation.

2. Open the repository in Claude Code.

3. Run:

   ```text
   /setup
   ```

4. Confirm the extracted profile summary.

The setup workflow reads the CV, extracts available information, and asks short follow-up questions only when information is missing, uncertain, or conflicting.

It collects the fields needed for fit evaluation and applications, including contact details, location, target roles, experience, skills, work authorization, and sponsorship needs.

## Profile storage

The repository includes a safe committed template:

```text
data/candidate-profile/candidate-profile.template.md
```

After confirmation, `/setup` creates your private completed profile:

```text
data/candidate-profile/candidate-profile.md
```

The completed profile is the source of truth for later workflows. Candidate facts are never inferred as confirmed information.

## Updating an existing profile

Run `/setup` again whenever information changes.

If `candidate-profile.md` already exists, the workflow preserves confirmed information and asks what you want to update. A new CV is not required unless it is needed to support a new or corrected fact.

## Privacy

Do not commit your original CV or completed profile. Both should be excluded through `.gitignore`.
