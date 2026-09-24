"""QA only: make modified temporary XLSX copies for independent recalculation."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree
from datetime import date,timedelta
import json,sys
ROOT=Path(__file__).resolve().parents[2]
QA=ROOT/'tmp/implementation-qa'
IN=QA/'recalc-input';OUT=QA/'recalc-output'
IN.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
S='{'+NS['s']+'}'
base=ROOT/'output/multimodal-implementation/Broadbridge_Multimodal_Implementation_Gantt.xlsx'
def value(z,sheet,cell):
    tr=etree.fromstring(z.read(f'xl/worksheets/sheet{sheet}.xml'))
    v=tr.find(f'.//s:c[@r="{cell}"]/s:v',NS)
    return v.text if v is not None else None
if len(sys.argv)==1:
    for name,sheet,cell,v in [('duration',3,'F75',3),('kickoff',1,'B5',(date(2026,10,5)-date(1899,12,30)).days)]:
        with ZipFile(base) as src,ZipFile(IN/f'{name}.xlsx','w',ZIP_DEFLATED) as dst:
            for item in src.infolist():
                raw=src.read(item.filename)
                if item.filename==f'xl/worksheets/sheet{sheet}.xml':
                    tr=etree.fromstring(raw);c=tr.find(f'.//s:c[@r="{cell}"]',NS)
                    assert c is not None
                    c.attrib.pop('t',None)
                    for child in list(c):c.remove(child)
                    etree.SubElement(c,S+'v').text=str(v)
                    raw=etree.tostring(tr,xml_declaration=True,encoding='UTF-8',standalone=True)
                if item.filename=='xl/workbook.xml':
                    tr=etree.fromstring(raw);calc=tr.find('s:calcPr',NS)
                    if calc is None:calc=etree.SubElement(tr,S+'calcPr')
                    calc.set('calcMode','auto');calc.set('fullCalcOnLoad','1');calc.set('forceFullCalc','1')
                    raw=etree.tostring(tr,xml_declaration=True,encoding='UTF-8',standalone=True)
                dst.writestr(item,raw)
    print('Created temporary duration and kickoff test copies')
else:
    with ZipFile(OUT/'duration.xlsx') as z:
        assert float(value(z,3,'F75'))==3
        assert float(value(z,3,'L75'))==154,value(z,3,'L75')
        assert float(value(z,1,'B7'))==154,value(z,1,'B7')
    end=date(2026,10,5);n=1
    while n<152:
        end+=timedelta(days=1)
        if end.weekday()<5:n+=1
    with ZipFile(OUT/'kickoff.xlsx') as z:
        assert float(value(z,1,'B12'))==(end-date(1899,12,30)).days,value(z,1,'B12')
        assert float(value(z,3,'M6'))==(date(2026,10,5)-date(1899,12,30)).days
    with ZipFile(base) as z:
        assert value(z,1,'B5') in [None,'']
        assert float(value(z,1,'B7'))==152
        assert float(value(z,3,'F75'))==1
    print(json.dumps({'office_recalculation':'passed','duration_change_finish_day':154,'test_kickoff':'2026-10-05','expected_test_finish':str(end),'delivered_workbook_kickoff':'blank','delivered_workbook_finish_day':152}))
