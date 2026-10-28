"""Country/account/group identity, mixed specialties and preservation of existing data."""
import unittest
import test_api

class CountryStandardTests(unittest.TestCase):
    def setUp(self):
        self.f=test_api.PulseTests();self.f.setUp()
    def tearDown(self):self.f.tearDown()
    def account(self,code='BNTE',country='MX'):
        return self.f.post('/api/accounts',{'code':code,'country_code':country,'name':'Cuenta '+code})['id']
    def state(self):return self.f.client.get('/api/state').json()
    def test_account_first_many_accounts_managers_and_mixed_specialties(self):
        aid=self.account();other=self.account('ACME');usa=self.account('BNTE','US')
        self.assertEqual(len({aid,other,usa}),3)
        m,_,_=self.f.person('MANAGER','M001',account=aid)
        m2,_,_=self.f.person('MANAGER','M002',account=aid)
        ids=[]
        for platform,key in [('MF','CICS/MQ'),('MF','Db2'),('MF','z/OS'),('OPEN','SO Linux'),('OPEN','Unix'),('OPEN','BD Oracle'),('OPEN','Linux')]:
            ids.append(self.f.post('/api/groups',{'account_id':aid,'manager_id':m['id'],'platform_code':platform,'service_key':key,'name':key})['id'])
        groups={g['id']:g for g in self.state()['groups']}
        expected=['MX-BNTE-MF-CICS-MQ','MX-BNTE-MF-DB2','MX-BNTE-MF-ZOS','MX-BNTE-OPEN-LINUX','MX-BNTE-OPEN-UNIX','MX-BNTE-OPEN-ORACLE','MX-BNTE-OPEN-LINUX-02']
        self.assertEqual([groups[i]['display_code'] for i in ids],expected)
        tech,_,_=self.f.person('USER','T001',group=ids[0])
        result=self.f.client.put('/api/groups/'+ids[0],json={**groups[ids[0]],'manager_id':m2['id'],'transfer_reason':'Reorganizar cobertura'})
        self.assertEqual(result.status_code,200,result.text)
        saved=next(g for g in self.state()['groups'] if g['id']==ids[0])
        self.assertEqual(saved['display_code'],expected[0]);self.assertEqual(saved['manager_id'],m2['id'])
        self.assertEqual(next(p for p in self.state()['people'] if p['id']==tech['id'])['group_id'],ids[0])
    def test_legacy_keys_history_and_memberships_survive_additive_metadata(self):
        aid=self.f.account('BNTE');gid=self.f.group(aid,'LEGACY');m,mc,_=self.f.person('MANAGER','M001',account=aid,groups=[gid]);u,uc,_=self.f.person('USER','T001',group=gid)
        oid=self.f.ot(uc)
        result=self.f.client.put('/api/accounts/'+aid,json={'code':'BNTE','name':'Banorte','country_code':'MX'})
        self.assertEqual(result.status_code,200,result.text)
        result=self.f.client.put('/api/groups/'+gid,json={'account_id':aid,'manager_id':m['id'],'platform_code':'OPEN','service_key':'Oracle','name':'Oracle'})
        self.assertEqual(result.status_code,200,result.text)
        group=next(g for g in self.state()['groups'] if g['id']==gid)
        self.assertEqual(group['code'],'LEGACY');self.assertEqual(group['display_code'],'MX-BNTE-OPEN-ORACLE')
        self.f.server.init_db()
        with self.f.server.connection() as c:
            self.assertEqual(c.execute('SELECT user_id FROM overtime WHERE id=?',(oid,)).fetchone()[0],u['id'])
            self.assertEqual(c.execute('SELECT group_id FROM users WHERE id=?',(u['id'],)).fetchone()[0],gid)
    def test_invalid_country_platform_foreign_manager_and_identity_change_rejected(self):
        self.assertEqual(self.f.client.post('/api/accounts',json={'code':'X','name':'X','country_code':'ZZ'}).status_code,422)
        aid=self.account();other=self.account('OTHER');m,_,_=self.f.person('MANAGER','M001',account=other)
        data={'account_id':aid,'manager_id':None,'platform_code':'OPEN','service_key':'Linux','name':'Linux'}
        self.assertEqual(self.f.client.post('/api/groups',json={**data,'platform_code':'INVALID'}).status_code,422)
        self.assertEqual(self.f.client.post('/api/groups',json={**data,'manager_id':m['id']}).status_code,422)
        self.f.post('/api/groups',data)
        self.assertEqual(self.f.client.put('/api/accounts/'+aid,json={'code':'BNTE','country_code':'US','name':'Banorte'}).status_code,422)
        self.assertEqual(self.f.client.post('/api/accounts',json={'code':'BNTE','country_code':'MX','name':'Duplicate'}).status_code,409)
