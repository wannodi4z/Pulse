"""History export is a filtered record list, separate from approved-hours analytics."""
import io
from fastapi import Depends,Request
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill

def install_record_exports(app,n):
 def workbook(report):
  wb=Workbook();sheet=wb.active;sheet.title='Registros'
  sheet.append(['Employee ID','Técnico','Grupo','Tipo','Referencia','Descripción','Inicio','Fin','Estado','Fecha de registro'])
  safe=lambda v:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v
  for r in report['records']:sheet.append([safe(r[k]) for k in ('employee_id','name','group_name','capture_type','reference','description','from_at','to_at','display_status','created_at')])
  context=wb.create_sheet('Filtros');context.append(['Criterio','Valor']);context.append(['Meses',', '.join(report['months'])]);context.append(['Total registros',report['record_count']])
  for k,v in report['filters'].items():context.append([k,safe(str(v or ''))])
  for s in wb:
   for cell in s[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='1C5185')
   s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
   for col in s.columns:s.column_dimensions[col[0].column_letter].width=25
  data=io.BytesIO();wb.save(data);data.seek(0)
  return StreamingResponse(data,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="Operational_Pulse_Registros_'+report['month']+'.xlsx"'})
 @app.get('/api/records.xlsx')
 def records(month:str,user_id:str|None=None,group_id:str|None=None,q:str='',status:str='',record_type:str='',months:str|None=None,period:str='MONTH',manager_id:str|None=None,dpe_id:str|None=None,actor=Depends(n['current_user'])):
  with n['connection']() as c:return workbook(n['analytics_report'](c,actor,month,user_id,group_id,query=q,status=status,record_type=record_type,months=months,period=period,manager_id=manager_id,dpe_id=dpe_id))
 @app.get('/api/my-records.xlsx')
 def personal(request:Request,month:str,q:str='',status:str='',record_type:str='',months:str|None=None,period:str='MONTH',actor=Depends(n['current_user'])):
  n['personal_analytics_query'](request)
  with n['connection']() as c:return workbook(n['analytics_report'](c,actor,month,personal=True,query=q,status=status,record_type=record_type,months=months,period=period))
