# Custom Commands - User Acceptance Testing Guide

## Overview

This guide provides instructions for testing the Custom Slash Commands feature interactively to ensure it meets user requirements and provides a great user experience.

## Prerequisites

1. OpenFatture installed and configured
2. Example commands installed:
   ```bash
   mkdir -p ~/.openfatture/commands/
   cp docs/examples/custom-commands/*.yaml ~/.openfatture/commands/
   ```
3. Database with some sample data (optional but recommended)

## Test Environment Setup

### 1. Start Interactive Chat

```bash
openfatture ai chat
```

You should see the welcome message and command prompt.

### 2. Verify Commands Are Loaded

Type `/custom` to list all available custom commands.

**Expected Output:**
```
📚 CUSTOM COMMANDS

Invoicing (2 commands):
  /fattura-rapida (aliases: fr, fattura)
    - Crea fattura completa con workflow AI

  /compliance-check (aliases: cc, check, verifica)
    - Verifica rapida compliance fattura

Clients (1 command):
  /cliente-info (aliases: ci, client, cliente)
    - Recupera informazioni complete su un cliente

Tax (1 command):
  /iva (aliases: vat, aliquota)
    - Suggerisci aliquota IVA e trattamento fiscale

Reporting (1 command):
  /report-mensile (aliases: rm, monthly-report, report)
    - Genera report mensile completo

Total: 5 custom commands loaded
```

**✅ Pass Criteria:**
- All 5 example commands are listed
- Commands are grouped by category
- Aliases are shown correctly
- Descriptions are clear and concise

## Test Cases

### Test Case 1: Invoice Creation with /fattura-rapida

**Objective:** Verify complete invoice workflow with AI assistance

**Steps:**
1. Type: `/fattura-rapida "Test Client SRL" "Web consulting 5h" "500"`
2. Press Enter

**Expected Behavior:**
- Command expands showing the full prompt preview
- AI processes the request
- Response includes:
  - Professional invoice description
  - VAT rate suggestion (22% for professional services)
  - Compliance check result
  - Confirmation prompt

**Verification:**
- [ ] Command expands correctly with all 3 arguments
- [ ] AI generates professional Italian description
- [ ] IVA suggestion is appropriate (22% for services)
- [ ] Compliance status is indicated (✅ or ⚠️)
- [ ] Response is formatted clearly with sections

**Edge Cases:**
- Try with special characters: `/fr "Test & Co." "Design + Dev" "1.000,50"`
- Try with missing argument: `/fr "Client" "Service"` (should handle gracefully)

---

### Test Case 2: Client Lookup with /cliente-info

**Objective:** Verify client information retrieval

**Steps:**
1. Type: `/cliente-info "Acme"`
2. Press Enter

**Expected Behavior:**
- Command expands with search query
- AI searches for client in database
- Response includes:
  - Client details (P.IVA, address, etc.)
  - Invoice statistics
  - Payment status
  - Recent invoices

**Verification:**
- [ ] Command expands correctly
- [ ] AI finds client (if exists in DB)
- [ ] Response is well-formatted with sections
- [ ] Statistics are accurate
- [ ] Warnings for overdue invoices are highlighted

**Aliases Test:**
- Try `/ci "Acme"` (should work identically)
- Try `/client "Acme"` (should work identically)

---

### Test Case 3: VAT Suggestion with /iva

**Objective:** Verify VAT rate suggestion for services

**Steps:**
1. Type: `/iva "IT consulting for construction company"`
2. Press Enter

**Expected Behavior:**
- Command expands with service description
- AI analyzes the service
- Response includes:
  - Suggested VAT rate with percentage
  - Legal justification (DPR 633/72)
  - Special regime checks (reverse charge, split payment)
  - Invoice notes suggestions

**Verification:**
- [ ] Command expands correctly
- [ ] AI provides specific VAT rate (e.g., 22%)
- [ ] Explanation references Italian tax law
- [ ] Special cases are analyzed (PA, reverse charge)
- [ ] Practical suggestions for invoice notes

**Different Services:**
- Try professional services: `/iva "Legal consulting"`
- Try goods: `/iva "Sale of computer hardware"`
- Try educational services: `/iva "Professional training course"`

---

### Test Case 4: Compliance Check with /compliance-check

**Objective:** Verify invoice compliance verification

**Steps:**
1. Type: `/compliance-check "2025-042"`
2. Press Enter

**Expected Behavior:**
- Command expands with invoice number
- AI performs comprehensive checks:
  1. Formal validation
  2. Invoice lines validation
  3. Fiscal treatment verification
  4. SDI compliance check
  5. Best practices review
- Response includes overall status and acceptance probability

**Verification:**
- [ ] Command expands correctly
- [ ] All 5 check sections are present
- [ ] Each check shows status (✅/⚠️/❌)
- [ ] Issues are clearly explained with solutions
- [ ] Acceptance probability is provided (0-100%)
- [ ] Final status is clear (READY/REQUIRES FIXES/NON-COMPLIANT)

**Aliases Test:**
- Try `/cc "2025-042"` (should work identically)
- Try `/verifica "2025-042"` (should work identically)

---

### Test Case 5: Monthly Report with /report-mensile

**Objective:** Verify comprehensive monthly business report

**Steps:**
1. Type: `/report-mensile Ottobre 2025`
2. Press Enter

**Expected Behavior:**
- Command expands with month and year
- AI generates comprehensive report:
  1. Invoicing metrics
  2. Payment metrics
  3. Top clients analysis
  4. Fiscal analysis
  5. Insights and recommendations
- Response uses tables, bullets, and highlights

**Verification:**
- [ ] Command expands correctly with month/year
- [ ] All 5 report sections are present
- [ ] Metrics are formatted clearly (€, %, numbers)
- [ ] Top clients are ranked
- [ ] Insights provide actionable recommendations
- [ ] Response uses emojis for visual clarity

**Different Months:**
- Try current month: `/rm`
- Try Italian month name: `/report-mensile Settembre`
- Try with year: `/rm December 2024`

---

### Test Case 6: Command Help System

**Objective:** Verify help and documentation access

**Steps:**
1. Type: `/help`
2. Verify custom commands are documented

**Expected Behavior:**
- Help shows both built-in and custom commands
- Custom commands section is clearly marked
- `/custom` command is listed for detailed info

**Verification:**
- [ ] Help is comprehensive and clear
- [ ] Custom commands are documented
- [ ] Examples are provided
- [ ] `/custom` command is mentioned

---

### Test Case 7: Command Reload

**Objective:** Verify hot-reload functionality

**Steps:**
1. Edit a command file: `~/.openfatture/commands/fattura-rapida.yaml`
2. Change the description
3. Type: `/reload`
4. Type: `/custom`
5. Verify the description changed

**Expected Behavior:**
- `/reload` command reloads all commands
- Changes are reflected immediately
- No need to restart chat

**Verification:**
- [ ] Reload completes quickly (< 1 second)
- [ ] Success message is shown
- [ ] Changes are reflected in `/custom` output
- [ ] Modified commands work correctly

---

### Test Case 8: Session Persistence

**Objective:** Verify conversation context is maintained

**Steps:**
1. Execute: `/cliente-info "Test Client"`
2. Execute: `/fattura-rapida "Test Client" "Consulting" "500"`
3. Ask: "Can you create the invoice for the client we just looked up?"

**Expected Behavior:**
- AI remembers the client from step 1
- AI can reference previous commands
- Session maintains context across custom commands

**Verification:**
- [ ] AI recalls previous client lookup
- [ ] Response references previous conversation
- [ ] Context is maintained appropriately
- [ ] No loss of information between commands

---

### Test Case 9: Error Handling

**Objective:** Verify graceful error handling

**Steps:**
1. Try invalid command: `/nonexistent`
2. Try command with wrong arguments: `/fattura-rapida`
3. Try command with special chars: `/fr "Test<script>alert()</script>" "Hack" "0"`

**Expected Behavior:**
- Invalid commands show helpful error message
- Missing arguments are handled gracefully (not crash)
- Special characters don't cause issues
- User is guided to correct usage

**Verification:**
- [ ] Invalid commands show clear error
- [ ] Missing arguments don't crash
- [ ] Special characters are sanitized
- [ ] Help is offered for errors
- [ ] No security issues (XSS, injection, etc.)

---

### Test Case 10: Performance and Responsiveness

**Objective:** Verify system performs well under normal use

**Steps:**
1. Execute 5 different custom commands in sequence
2. Measure approximate response times
3. Check system resource usage

**Expected Behavior:**
- Each command responds in < 5 seconds (excluding AI inference)
- No noticeable lag or freezing
- Memory usage stays reasonable
- No error accumulation

**Verification:**
- [ ] Command expansion is instant (< 100ms)
- [ ] AI responses are reasonable (< 10s for typical LLM)
- [ ] No memory leaks over multiple commands
- [ ] UI remains responsive
- [ ] No degradation after multiple uses

---

## Acceptance Criteria

The Custom Commands feature is **ACCEPTED** if:

### Functional Requirements ✅
- [ ] All 5 example commands load and execute correctly
- [ ] Command aliases work identically to main command names
- [ ] Command expansion shows preview before AI processing
- [ ] AI responses are contextually appropriate for each command
- [ ] Session context is maintained across commands
- [ ] Hot-reload works without restarting chat

### Usability Requirements ✅
- [ ] Commands are easy to discover (`/custom`, `/help`)
- [ ] Error messages are clear and actionable
- [ ] Response formatting is clear and professional
- [ ] Italian language responses are grammatically correct
- [ ] Visual aids (emojis, tables, bullets) enhance readability

### Performance Requirements ✅
- [ ] Command expansion < 5ms (measured in benchmarks)
- [ ] Registry loading < 100ms for 50 commands
- [ ] No noticeable lag in interactive use
- [ ] Memory usage stays under 50MB for typical session

### Quality Requirements ✅
- [ ] No crashes or unhandled exceptions
- [ ] Special characters handled safely
- [ ] No security vulnerabilities (XSS, injection)
- [ ] Logging is appropriate (not too verbose, not missing errors)

---

## Known Limitations

1. **AI Model Dependency**: Response quality depends on the configured AI provider and model
2. **Database Access**: Some commands require database with sample data
3. **Italian Context**: Commands are designed for Italian invoicing context
4. **Manual Reload**: Users must run `/reload` after editing command files

---

## Reporting Issues

If you encounter issues during testing:

1. **Check Logs**: Look for errors in console output
2. **Verify Setup**: Ensure commands are in `~/.openfatture/commands/`
3. **Test Isolation**: Try command individually to isolate issue
4. **Document**: Note exact command, expected vs actual behavior
5. **Report**: Create GitHub issue with reproduction steps

---

## Success Metrics

After completing UAT, the feature should demonstrate:

- **Discovery**: Users can easily find and learn about custom commands
- **Execution**: Commands work reliably and produce expected results
- **Flexibility**: Users can create their own commands following examples
- **Performance**: System remains responsive under typical workloads
- **Reliability**: No crashes, data loss, or critical errors

---

## Next Steps After UAT

1. **Document Findings**: Record any issues or improvements needed
2. **Create Tickets**: File GitHub issues for any bugs found
3. **Gather Feedback**: Collect user feedback on UX and workflow
4. **Iterate**: Make improvements based on testing results
5. **Deploy**: Merge to main branch if all criteria are met

---

## UAT Sign-Off

**Tester**: ___________________________
**Date**: ___________________________
**Result**: ⬜ PASS  ⬜ PASS WITH ISSUES  ⬜ FAIL
**Notes**: ___________________________

---

**Version**: 1.0
**Last Updated**: 2025-10-16
**Sprint**: Sprint 1 - Custom Slash Commands
