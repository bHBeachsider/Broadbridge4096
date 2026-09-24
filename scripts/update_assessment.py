from pathlib import Path

root=Path(__file__).resolve().parents[1]
path=root/'Oil-and-Gas-Expert-Knowledge-Business-Assessment.md'
text=path.read_text(encoding='utf-8')
backup=root/'tmp'/'assessment-before-subsidiary-update.md'
if not backup.exists(): backup.write_text(text,encoding='utf-8')
text=text.replace('# Expert knowledge business for refining and gas processing','# Broadbridge Oil & Gas subsidiary business assessment')
old='**Recommendation.** Develop an expert-led business for refinery process troubleshooting and engineering development, beginning with one tightly defined equipment family.'
new='**Recommendation.** Develop **Broadbridge Oil & Gas** as a dedicated, initially 100%-owned subsidiary of **Broadbridge4096**, combining expert advisory, AI software, training, and knowledge licensing. Serve the full oil and gas value chain through phased expansion, beginning with refinery process troubleshooting and engineering development in one tightly defined equipment family.'
assert old in text
text=text.replace(old,new)
text=text.replace('Research and business assessment | 23 September 2026','Research and business assessment | 23 September 2026\n\nUpdated to the approved subsidiary organizational design. Broadbridge Oil & Gas is a working name; jurisdiction and final legal form remain for subsequent legal implementation.')
needle='These are planning documents, not proof of incorporation, committed financing, regulatory authorization, existing contracts, or deployed capabilities.'
text=text.replace(needle,'The Energy Trading documents are organizational references for a commodity business, not an ownership map or a requirement for the subsidiary to serve a trading operation. '+needle)
start=text.index('## 8 Fit with the supplied corporate structure')
end=text.index('## 9 A 90-day validation program')
replacement='''## 8 Broadbridge4096 subsidiary structure

**Broadbridge4096 is the explicit parent.** Establish Broadbridge Oil & Gas as its dedicated subsidiary, initially assuming 100% parent ownership. The business will own its customer delivery, product priorities, expert relationships, and operating results. Incorporation jurisdiction and final legal form remain a subsequent legal implementation decision. This organizational design does not presume that an entity has already been incorporated or that financing, appointments, or contracts have been executed.

The Energy Trading organization charts, business plan, strategy memo, and operating playbook supply examples of reporting lines, oversight, shared functions, and disciplined operating processes. Their trading desks, international entities, merchant financing, tax assumptions, and headcounts do not carry into this design. The subsidiary is an adjacent expert-services and product business serving its own external customers. [Original organization chart](<C:/Users/bradu/OneDrive/Documents/Claude/Projects/Energy Trading/Broadbridge_4096_Org_Chart.docx>), [Phase 3 organization chart](<C:/Users/bradu/OneDrive/Documents/Claude/Projects/Energy Trading/Broadbridge_4096_Org_Chart_Phase3_Agentic.docx>)

```mermaid
flowchart TD
    P[Broadbridge4096] -->|Initial ownership assumption 100 percent| B[Subsidiary Board]
    B --> MD[Managing Director]
    MD --> C[Commercial Director]
    MD --> T[Technical Director]
    MD --> A[Head of Product and AI]
    T --> E[Process Applications Engineer]
    A --> AI[Applied AI Engineer]
    A --> K[Knowledge Engineer]
    X[Contracted Expert Council] -. Advisory reporting .-> T
    X -. Direct escalation .-> B
    P --> S[Shared finance treasury legal HR IT security and administration]
    S -. Service agreement .-> MD
```

The seven employee positions are the Managing Director, Commercial Director, Technical Director, Process Applications Engineer, Head of Product & AI, Applied AI Engineer, and Knowledge Engineer. Expert Council members and independent reviewers are contractors. Parent shared-service personnel and board participation are outside dedicated employee totals. Norman Lieberman remains an **illustrative founding expert candidate**, without an implied appointment, endorsement, or agreed license.

### Practices and offerings

| Practice | Sequence and scope |
|---|---|
| Downstream and Petrochemicals | Launch in refining, process troubleshooting, equipment performance, and operating knowledge. The Technical Director leads the practice initially. |
| Gas Processing and Midstream | Subsequent expansion into treatment, compression, processing, LNG-related operations, and facilities with a dedicated practice lead and suitable experts. |
| Upstream Production and Facilities | Later expansion with its own specialists. Drilling and subsurface services require separately demonstrated capability. |

Each practice can sell four offerings within its accepted technical scope: advisory engagements, recurring software subscriptions, training programs, and licensed expert knowledge. Commercial and product teams serve the practices across the subsidiary. A practice is not a separate legal entity under this design.

### Decision rights and shared services

| Decision | Accountable owner | Boundary |
|---|---|---|
| Capital allocation, annual budget, senior appointments, equity changes, material IP transactions | Broadbridge4096 | Subsidiary Board recommends and oversees execution. |
| Customer commitments and operating execution | Managing Director | Within a written delegation; route commitments to the parent through the board until limits are approved. |
| Technical scope, acceptance, and suspension | Technical Director | May stop unsupported or unsafe deliverables; independent review is required for material technical work. |
| Product implementation and release | Head of Product & AI | Release requires Technical Director acceptance and acceptance by the designated parent IT security lead. |
| Customer delivery | Technical Director at launch; Delivery Lead after appointment | One accountable delivery owner per engagement, with a documented transition. Technical acceptance stays with the Technical Director. |
| Independent review findings | Assigned independent reviewer | Reviewers cannot certify their own authored material or implementation. |

The Expert Council reports to the Technical Director with direct escalation to the Subsidiary Board. It advises on domain coverage, methods, evidence, and limitations; membership provides no management or signing authority. Commercial deadlines cannot override technical or security stops.

Broadbridge4096 supplies finance, treasury, legal, HR, IT security, and corporate administration through defined service arrangements. Each arrangement identifies service owners, service levels, charges, access boundaries, and escalation. The Managing Director owns the subsidiary service relationship and P&L. Parent access to customer data follows permissions and operational need, not ownership alone.

### Expert participation and IP responsibilities

Use expert retainers, scoped fees, and licensing arrangements. Equity is a separate parent decision. Expert contracts must define background content, new case ownership or license, permitted uses, attribution, compensation, review duties, conflicts, continuity, and termination rights. Public availability or authorship does not establish all commercial rights.

Separate the three asset classes. Experts or actual rights holders retain pre-existing content unless expressly assigned; the subsidiary obtains specified licenses. New subsidiary-funded software should be assigned to the subsidiary through employment and contractor agreements, while parent or third-party components require licenses. Customers retain their contractual rights in supplied data; permission to deliver a project does not authorize general model training, publication, or cross-customer reuse.

The Knowledge Engineer maintains source and rights records. The Head of Product & AI maintains software records and enforces access restrictions. The Technical Director accepts technical content. The Managing Director approves contractual permissions within delegation on legal advice; material IP transactions remain parent reserved matters. Any potential reuse of parent or affiliated platforms requires diligence on ownership, support, cost, security, and sublicensing rather than an assumed transfer.

### Staffing stages

| Function | Launch | Expansion | Mature target |
|---|---:|---:|---:|
| Managing Director | 1 | 1 | 1 |
| Commercial | 1 | 2 | 3 |
| Technical practices | 2 | 4 | 7 |
| Product, AI, and knowledge engineering | 3 | 4 | 6 |
| Dedicated delivery and customer success | 0 | 2 | 4 |
| Dedicated academy team | 0 | 0 | 2 |
| Subsidiary business operations | 0 | 0 | 1 |
| **Dedicated employees** | **7** | **13** | **24** |

Launch staff cover delivery and training. Contractors and shared services are additional resource arrangements, not hidden employees within these totals. Expansion requires repeatable paid deployments, funded staffing, and a paid customer mandate for every new practice. The mature structure is a destination, not an immediate hiring commitment.

The editable [subsidiary organizational chart](C:/Users/bradu/Documents/Broadbridge4096/output/docx/Broadbridge_Oil_and_Gas_Organizational_Chart.docx) and [business and operating structure](C:/Users/bradu/Documents/Broadbridge4096/output/docx/Broadbridge_Oil_and_Gas_Business_and_Operating_Structure.docx) define reporting lines, exact future role mixes, governance, delivery workflow, and performance ownership. The original reference documents and Energy Trading folder link remain unchanged.

'''
text=text[:start]+replacement+text[end:]
old='The timing assumes expert availability and timely data permission. Customer procurement can extend it. A plausible planning envelope is $150,000–$250,000 for product and knowledge engineering, paid expert work, independent review, rights/security support, infrastructure, and contingency. Obtain actual quotes and model founder compensation explicitly; this is not a staffing estimate proven by market research.'
new='The timing assumes expert availability and timely data permission. Customer procurement can extend it. The earlier $150,000–$250,000 validation envelope is an illustrative hypothesis for a bounded prototype program, not an approved operating budget or a fully costed estimate for seven dedicated employees. Build a separate parent-approved cash plan using actual compensation assumptions, hiring dates, expert retainers, independent review, shared-service charges, infrastructure, working capital, and contingency before authorizing launch staffing.'
assert old in text
text=text.replace(old,new)
start=text.index('## 10 Decisions still needed')
text=text[:start]+'''## 10 Implementation decisions still needed

The adopted organizational design identifies Broadbridge4096 as parent, assumes initial 100% ownership, sets a seven-person launch team, and defines the 13- and 24-person staffing stages. Those are planning decisions, not evidence of legal formation, completed hiring, or capital commitment.

The next material inputs are the present relationship with Lieberman and other candidate experts; the content and client histories they can license; paid design-customer mandates; a costed staffing and cash plan; and written decision limits. Complete expert and software rights agreements, customer-data permissions, and the shared-service arrangements before deployment. Jurisdiction, final legal form, and any applicable professional-service authorizations remain legal implementation decisions.

The first investment decision should turn on **a committed expert, a usable rights package, and a paying customer with a measurable problem**. The Managing Director owns the investment recommendation, the parent approves capital and budget, and the Technical Director owns technical acceptance. Model training remains a subsequent engineering choice supported by evaluation results.
'''
path.write_text(text,encoding='utf-8')
readme=root/'README.md'
r=readme.read_text(encoding='utf-8')
links='''[Subsidiary organizational chart](C:/Users/bradu/Documents/Broadbridge4096/output/docx/Broadbridge_Oil_and_Gas_Organizational_Chart.docx)

[Business and operating structure](C:/Users/bradu/Documents/Broadbridge4096/output/docx/Broadbridge_Oil_and_Gas_Business_and_Operating_Structure.docx)

'''
if '[Subsidiary organizational chart]' not in r: r=r.replace('[Expert knowledge business assessment]',links+'[Expert knowledge business assessment]')
readme.write_text(r,encoding='utf-8')
print('Updated assessment and workspace index. Original assessment retained in tmp for comparison.')
