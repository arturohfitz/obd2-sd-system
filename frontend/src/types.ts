export type Customer={id:number;name:string;company?:string;phone:string;email?:string;status:'prospect'|'active'|'inactive';notes?:string;next_follow_up?:string;balance:number;created_at:string};
export type Product={id:number;name:string;category:string;price:number;active:boolean};
export type Sale={id:number;customer_id:number;customer_name:string;product_id?:number;concept:string;vehicle?:string;amount:number;paid:number;balance:number;status:string;sale_date:string;notes?:string};
export type PromiseItem={id:number;sale_id:number;amount:number;due_date:string;status:string;customer_name:string;concept:string;days_overdue:number};
export type Dashboard={total_sales:number;total_collected:number;total_receivable:number;overdue:number;due_today:number;due_next_7_days:number;active_customers:number;overdue_customers:number};
export type Activity={id:number;customer_id:number;activity_type:string;description:string;follow_up_date?:string;user_name:string;created_at:string};
export type CustomerFile={id:number;customer_id:number;original_name:string;content_type:string;size:number;description?:string;user_name:string;created_at:string};
export type CustomerDetail=Customer&{sales:Sale[];activities:Activity[];files:CustomerFile[]};
