# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from mana_api import db

# 流量主表
class netflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(80))
    total_in = db.Column(db.String(120))
    total_out = db.Column(db.String(120))
    max_in_rate = db.Column(db.Float)
    max_in_rate_date = db.Column(db.DateTime)
    max_out_rate = db.Column(db.Float)
    max_out_rate_date = db.Column(db.DateTime)
    region = db.Column(db.String(120))
    project_id = db.Column(db.String(120))

    def __repr__(self):
        return '<Project %s>' % self.project_id

# 流量详细表
class netrate_project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    in_rate = db.Column(db.Float)
    out_rate = db.Column(db.Float)
    begin_rate_date = db.Column(db.DateTime)
    end_rate_date = db.Column(db.DateTime)
    region = db.Column(db.String(80))
    project_id = db.Column(db.String(80))

    def __repr__(self):
        return '<Project(Detail) %r>' % self.project_id


# 物理机信息表
class pm_servers(db.Model):
    __bind_key__ = 'cloud'
    id = db.Column(db.Integer, primary_key=True)
    system_snid = db.Column(db.String(255))
    asset_id = db.Column(db.String(255))
    host_name = db.Column(db.String(255))
    system_type = db.Column(db.String(255))
    cpu_num = db.Column(db.Integer)
    mem_size = db.Column(db.Integer)
    disk_size = db.Column(db.Integer)
    ip = db.Column(db.String(255))
    tenant_id = db.Column(db.String(255))
    tenant_name = db.Column(db.String(255))
    region = db.Column(db.String(255))
    manufacturer = db.Column(db.String(255))
    deleted = db.Column(db.Integer)
    create_at = db.Column(db.DateTime)
    update_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Project(Detail) %r>' % self.tenant_name


# ilo 表
class pm_ilo_list(db.Model):
    __bind_key__ = 'cloud'
    id = db.Column(db.Integer, primary_key=True)
    system_snid = db.Column(db.String(255))
    asset_id = db.Column(db.String(255))
    ilo_ip = db.Column(db.String(255))
    ilo_user = db.Column(db.String(255))
    ilo_passwd = db.Column(db.String(255))
    status = db.Column(db.String(255))
    available = db.Column(db.Integer)
    create_at = db.Column(db.DateTime)
    update_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Project(Detail) %r>' % self.system_snid


# 计费表
class pm_accounts(db.Model):
    __bind_key__ = 'cloud'
    id = db.Column(db.Integer, primary_key=True)
    system_snid = db.Column(db.String(255))
    price = db.Column(db.Float)
    tenant_id = db.Column(db.String(255))
    region = db.Column(db.String(255))
    update_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Project(Detail) %r>' % self.system_snid


# 监控数据表
class pm_monitors(db.Model):
    __bind_key__ = 'cloud'
    id = db.Column(db.Integer, primary_key=True)
    system_snid = db.Column(db.String(255))
    info = db.Column(db.Text)
    update_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Project(Detail) %r>' % self.system_snid
