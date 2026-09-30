"""Render a local questionnaire draft from the frozen pressure-demo questions.

Writes static review material only. No model, database, cloud or deployment calls.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'packs/oil-gas/outputs/pressure-demo-v1'
OUT = ROOT / 'docs/questionnaires/pressure-training-v1'


def main():
    manifest_bytes = (PACKAGE / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    for name in ['demo_prompts.jsonl', 'demo_answer_key.jsonl']:
        if hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() != manifest['artifacts'][name]['sha256']:
            raise ValueError('Frozen demonstration input changed')
    prompts = [json.loads(line) for line in (PACKAGE / 'demo_prompts.jsonl').read_text(encoding='utf-8').splitlines()]
    keys = {row['question_id']: row for row in map(json.loads, (PACKAGE / 'demo_answer_key.jsonl').read_text(encoding='utf-8').splitlines())}
    categories = [
        {'id': 'priorities', 'title': 'Where this would help', 'intro': 'Identify and rank specific engineering tasks to determine the initial training scope.'},
        {'id': 'numbers', 'title': 'Numbers and pressure references', 'intro': 'Read the source notes and record the required answer before opening the draft reference. Check the calculation, units, pressure basis and assumptions.'},
        {'id': 'judgment', 'title': 'Missing facts and judgment', 'intro': 'Specify when the model should request information, explain a limitation or withhold a conclusion.'},
        {'id': 'experience', 'title': 'Exceptions, sources and Norm', 'intro': 'Identify cases, source material and expert contributions that would extend the training beyond the handbook examples.'},
        {'id': 'next', 'title': 'Your recommendation', 'intro': 'Specify revisions, acceptance criteria and additional tasks for the next demonstration.'},
    ]
    items = [
        {'id': 'PRIORITY-01', 'category': 'priorities', 'kind': 'open', 'title': 'What would you want help with first?',
         'question': 'Think of a recent job. Which check, investigation or document task took more effort than it should have? What happened, and who needed the result?',
         'help': 'Describe an actual task and remove identifying client details.', 'why': 'Select a useful first task before expanding the training corpus.', 'discovery_links': ['B01', 'C01']},
        {'id': 'PRIORITY-02', 'category': 'priorities', 'kind': 'open', 'title': 'Define a useful result',
         'question': 'For that task, complete: Given [inputs], help [person] prepare [output] so they can [decision]. What would you still check or decide yourself?',
         'help': 'Include the information usually missing, and the calculation or evidence you would expect to see.', 'why': 'Turn a broad priority into a trainable task and a reviewable output.', 'discovery_links': ['C01', 'C03', 'C04']},
        {'id': 'PRIORITY-03', 'category': 'priorities', 'kind': 'open', 'title': 'How would pressure checking rank?',
         'question': 'Where would checking pressure bases, units and missing assumptions rank against your other priorities? Describe how often errors arise, their consequence and the review effort. Suggest a more valuable starting topic if appropriate.',
         'help': 'State the priority and basis for the ranking. Mark unknown frequency, effort or consequence explicitly.', 'why': 'Prioritize training tasks by practical value.', 'discovery_links': ['B02', 'C02', 'E03']},
    ]
    titles = ['Gauge to absolute', 'Negative gauge pressure', 'A positive vacuum reading',
              'An ambiguous “psi” value', 'Equal numbers, different references',
              'Challenge a plausible sign error', 'When a pressure value is not enough',
              'Where the recipe stops']
    requirements = [
        ['Uses the supplied local atmospheric reference', 'Adds signed gauge pressure', 'Reports psia and shows the calculation'],
        ['Distinguishes gauge from absolute pressure', 'Preserves the negative sign in the input', 'Uses the applicable atmospheric reference'],
        ['States the positive-depression convention', 'Subtracts the depression from atmosphere', 'Reports the absolute-pressure basis'],
        ['Asks which pressure reference the number uses', 'Does not invent atmospheric pressure', 'Names the minimum information needed'],
        ['Preserves both original readings', 'Compares on a common pressure basis', 'Does not declare operating acceptability'],
        ['Explains the sign convention', 'Uses only supplied evidence', 'Flags a convention that would change the result'],
        ['Withholds unsupported operating approval', 'Names the missing design and operating evidence', 'Identifies when an engineer must decide'],
        ['Recognizes the mass/force convention issue', 'Does not silently rewrite the source', 'States what would permit the calculation'],
    ]
    for i, prompt in enumerate(prompts):
        key = keys[prompt['question_id']]
        items.append({'id': prompt['question_id'], 'category': 'numbers' if i < 3 else 'judgment',
            'kind': 'example', 'title': titles[i], 'type': prompt['type'],
            'question': prompt['messages'][1]['content'].split('\n\nTask: ', 1)[1],
            'evidence_note': prompt['messages'][1]['content'].split('\n\nTask: ', 1)[0],
            'help': 'State the required calculations, assumptions, evidence and follow-up questions.',
            'reference_answer': key['reference_answer'], 'hard_fail_criteria': key['hard_fail_criteria'],
            'tolerance': key['tolerance'], 'requirements': requirements[i],
            'graphic': 'gauge' if i == 0 else 'negative_gauge' if i == 1 else 'vacuum' if i == 2 else 'references' if i == 4 else None,
            'source_url': 'https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35',
            'source_label': 'DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)',
            'why': 'Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.',
            'independent_test': False})
    items += [
        {'id': 'EXPERIENCE-01', 'category': 'experience', 'kind': 'open', 'title': 'Where would the obvious answer fail?',
         'question': 'Describe a case where a familiar rule or plausible diagnosis misled people. What was known initially, what was missing, and what observation changed the conclusion? Where does the lesson stop applying?',
         'help': 'Distinguish something you observed from a reconstructed memory or hypothetical example. Identify client records by description only.', 'why': 'Find rare but consequential cases; keep initial evidence separate from hindsight.', 'discovery_links': ['D01', 'D02', 'D04', 'D05']},
        {'id': 'EXPERIENCE-02', 'category': 'experience', 'kind': 'open', 'title': 'Where could Norm help most?',
         'question': 'Which two or three problems would you ask Norm about first? What would you ask him to explain that a handbook leaves out? If interested, would his best next contribution be a case, a critique of answers, a teaching discussion, or something else?',
         'help': 'Name another specialist if the task requires different expertise.', 'why': 'Begin with focused expertise before discussing broader archive access.', 'discovery_links': ['F01']},
        {'id': 'EXPERIENCE-03', 'category': 'experience', 'kind': 'open', 'title': 'What evidence would improve the examples?',
         'question': 'Which report, drawing, datasheet, calculation, teaching note or resolved discussion would help? What would it teach, who likely owns it, and what restrictions might apply?',
         'help': 'Nominate material; do not paste private records or assume that access grants training permission.', 'why': 'Build a source shortlist with ownership and scope, separate from rights approval.', 'discovery_links': ['C07']},
        {'id': 'NEXT-01', 'category': 'next', 'kind': 'open', 'title': 'What would earn your confidence?',
         'question': 'What should the next demonstration show before you would use an assistant’s draft? Name a useful result, a failure that would stop you using it, and the person who should review it.',
         'help': 'Suggest one small input package and one observable success criterion.', 'why': 'Set task-specific acceptance criteria rather than relying on a general accuracy percentage.', 'discovery_links': ['E03', 'C05']},
        {'id': 'NEXT-02', 'category': 'next', 'kind': 'open', 'title': 'What have we missed?',
         'question': 'Add tasks, exceptions, corrections or questions not covered above. Enter notes or paste a transcript.',
         'help': 'This draft supports text and pasted transcripts. The separate voice-intake work can supply reviewed transcript passages later.', 'why': 'Record additional tasks and exceptions for follow-up.', 'discovery_links': ['B03', 'F02']},
    ]
    data = {'schema': 'broadbridge.training_questionnaire_draft/1', 'id': 'pressure-training-v1',
            'version': 1, 'status': 'draft_not_deployed', 'title': 'Engineering training review',
            'introduction': 'The purpose of this exercise is to define the model’s priority tasks, reference answers and evaluation criteria. Work through the five sections. For each example, read the source notes, record the required answer, then compare it with the draft reference. Identify corrections, missing evidence and serious errors. Add cases or topics the training should cover, then download your responses.',
            'reviewer': '', 'estimated_time': 'About 10 minutes for a first pass; 20–30 minutes for all examples.',
            'source_package_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
            'training_approved': False, 'rights_status': 'TBD', 'categories': categories, 'questions': items}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'questionnaire.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    lines = ['# Engineering training review — questionnaire draft', '', data['introduction'], '', data['estimated_time'], '',
             'Draft for an authenticated URL. The local preview is not a server-saved review, model score, signed case or permission grant. All reference answers are authored drafts, not Qwen outputs.', '',
             'For each example: write your expectation first; optionally reveal the draft answer; choose supported / needs correction / contradicted / insufficient evidence / outside my expertise; revise the reference or critical-error rule; identify essential checks.', '']
    for category in categories:
        lines += ['## '+category['title'], '', category['intro'], '']
        for item in items:
            if item['category'] != category['id']: continue
            lines += [f"### {item['id']} — {item['title']}", '', item['question'], '', item['help'], '']
            if item['kind']=='example':
                lines += ['**Source notes available to the model:** '+item['evidence_note'], '',
                          '['+item['source_label']+']('+item['source_url']+')', '',
                          '**Optional reveal — draft reference:** '+item['reference_answer'], '',
                          '**Proposed serious error:** '+item['hard_fail_criteria'], '',
                          '**Checks Bill can mark essential / optional / revise / unsure:**', '']
                lines += ['- '+r for r in item['requirements']]
                lines += ['', '**Tolerance:** '+item['tolerance'], '']
            lines += ['**Purpose:** '+item['why'], '']
    (OUT / 'QUESTIONS.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    print(json.dumps({'questions': len(items), 'examples': len(prompts), 'categories': len(categories), 'deployed': False}))


if __name__ == '__main__':
    main()
