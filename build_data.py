#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тягне дані з Databricks у report_data.json.
Потрібні env-змінні:
  DATABRICKS_HOST       (напр. bolt-common.cloud.databricks.com)
  DATABRICKS_TOKEN      (dapi...)
  DATABRICKS_WAREHOUSE_ID
Запуск:  python3 build_data.py
"""
import json, os, time, urllib.request, sys

HOST=os.environ.get("DATABRICKS_HOST"); TOKEN=os.environ.get("DATABRICKS_TOKEN"); WID=os.environ.get("DATABRICKS_WAREHOUSE_ID")
if not (HOST and TOKEN and WID):
    sys.exit("Set env: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID")
GROUPS=['VARUS','KOPIYKA','LOKO','HOP HEY','RUKAVYCHKA','BEER MARKET']
inlist=",".join("'%s'"%g for g in GROUPS)
START=os.environ.get("DATA_START","2026-01-01"); END=os.environ.get("DATA_END","2026-05-31")

def run(sql):
    body=json.dumps({"warehouse_id":WID,"statement":sql,"wait_timeout":"50s","format":"JSON_ARRAY"}).encode()
    req=urllib.request.Request("https://%s/api/2.0/sql/statements"%HOST,data=body,
        headers={"Authorization":"Bearer %s"%TOKEN,"Content-Type":"application/json"})
    d=json.load(urllib.request.urlopen(req)); sid=d["statement_id"]
    while d["status"]["state"] in ("PENDING","RUNNING"):
        time.sleep(3)
        d=json.load(urllib.request.urlopen(urllib.request.Request(
            "https://%s/api/2.0/sql/statements/%s"%(HOST,sid),headers={"Authorization":"Bearer %s"%TOKEN})))
    if d["status"]["state"]!="SUCCEEDED": raise SystemExit("FAIL "+json.dumps(d["status"]))
    return d.get("result",{}).get("data_array",[]) or []

M="""
 SUM(f.total_gmv_before_discounts_eur) gmv,
 SUM(f.provider_impressions_sessions_count) impr,
 SUM(f.provider_menu_viewed_sessions_count) viewed,
 SUM(f.provider_product_added_sessions_count) added,
 SUM(f.provider_order_placed_sessions_count) placed,
 SUM(f.delivered_orders_count) delivered,
 SUM(f.users_activated_brand_count) ua_brand,
 SUM(f.users_activated_city_count) ua_city,
 SUM(f.gmv_before_discounts_per_order_eur_value*f.gmv_before_discounts_per_order_eur_weight)/NULLIF(SUM(f.gmv_before_discounts_per_order_eur_weight),0) aov,
 SUM(f.basket_items_per_order_value*f.basket_items_per_order_weight)/NULLIF(SUM(f.basket_items_per_order_weight),0) basket,
 SUM(f.delivery_30d_retention_rate_value*f.delivery_30d_retention_rate_weight)/NULLIF(SUM(f.delivery_30d_retention_rate_weight),0)*100 ret30,
 SUM(f.same_provider_30d_retention_rate_value*f.same_provider_30d_retention_rate_weight)/NULLIF(SUM(f.same_provider_30d_retention_rate_weight),0)*100 retsp
"""
FPW="""FROM hive_metastore.ng_delivery_spark.fact_provider_weekly f
JOIN hive_metastore.ng_delivery_spark.dim_provider_v2 p ON f.provider_id=p.provider_id
WHERE p.country_code='ua' AND p.group_name IN (%s)
 AND f.metric_timestamp_local>='%s' AND f.metric_timestamp_local<='%s'"""%(inlist,START,END)
CJ=" JOIN hive_metastore.ng_delivery_spark.dim_delivery_city c ON p.city_id=c.city_id"
FPWc=FPW.replace("ON f.provider_id=p.provider_id","ON f.provider_id=p.provider_id"+CJ)

totals=run("SELECT p.group_name, DATE_FORMAT(f.metric_timestamp_local,'yyyy-MM') ym, %s, COUNT(DISTINCT f.provider_id) stores %s GROUP BY 1,2"%(M,FPW))
cities=run("SELECT p.group_name, DATE_FORMAT(f.metric_timestamp_local,'yyyy-MM') ym, c.city_name, %s %s GROUP BY 1,2,3"%(M,FPWc))
stores=run("SELECT p.group_name, DATE_FORMAT(f.metric_timestamp_local,'yyyy-MM') ym, p.provider_name, c.city_name, %s %s GROUP BY 1,2,3,4"%(M,FPWc))
cons=run("""SELECT p.group_name, DATE_FORMAT(f.order_created_date,'yyyy-MM') ym,
 COUNT(*) orders, COUNT(DISTINCT f.user_id) active_users,
 COUNT(DISTINCT CASE WHEN f.is_first_delivery_order THEN f.user_id END) new_users
FROM hive_metastore.ng_delivery_spark.fact_order_delivery f
JOIN hive_metastore.ng_delivery_spark.dim_provider_v2 p ON f.provider_id=p.provider_id
WHERE p.country_code='ua' AND p.group_name IN (%s) AND f.order_state='delivered'
 AND f.order_created_date>='%s' AND f.order_created_date<='%s' GROUP BY 1,2"""%(inlist,START,END))

json.dump({"totals":totals,"cities":cities,"stores":stores,"cons":cons},
          open(os.path.join(os.path.dirname(__file__),"report_data.json"),"w"),ensure_ascii=False)
print("totals",len(totals),"cities",len(cities),"stores",len(stores),"cons",len(cons))
