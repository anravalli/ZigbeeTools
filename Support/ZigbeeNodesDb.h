
#ifndef ZB_NODE_DB_H
#define ZB_NODE_DB_H

#define UINT_8 unsigned char
#define UINT_16 unsigned int
#if int64
	//TODO check if the platform support 64 bit
	#define UINT_64 unsigned long long
	#define ADDR_64 UINT_64
#else
	typedef unsigned char ADDR_64[8];
#endif

#define MAX_NODES 15
#define MAX_NODE_EPOINTS 2
#define MAX_EP_CLS 7
#define ZB_EP_TABLE_SIZE  MAX_NODES * MAX_NODE_EPOINTS
#define ZB_CLS_TABLE_SIZE MAX_EPOINTS * MAX_EP_CLS

#define NO_MORE_NODES -1
#define NO_MORE_EP -2
#define NO_MORE_CLS -3

int ERROR_CODE = 0;

UINT_8 _next_node_idx = 0;
UINT_8 _next_ep_idx = 0;
UINT_8 _next_cluster_idx = 0;

#define CLS_TYPE_IN 0;
#define CLS_TYPE_OUT 1;

typedef struct zcl_cluster {
	UINT_16 zb_profile_id;
	UINT_16 zb_cls_id;
	UINT_8 cls_type_io;
	//TODO:
	//attr_list[MAX_ATTR]
	//cls_commands[]
} zcl_cluster_t;

typedef struct zb_epoint {
	UINT_16 zb_profile_id;
	UINT_16 zb_device_id;
	/*	TODO consider to split IN/OUT clusters
		To save memory the IN and OUT clusters are currently
		stored in the same list.
	*/
	UINT_8 next_cls;
	zcl_cluster_t * cls_list[MAX_EP_CLS];
} zb_epoint_t;

typedef struct zb_node {
	UINT_16 nwk_addr;
	ADDR_64 ieee_addr;
	ADDR_64 mac_address;
	UINT_8 next_ep;
	zb_epoint_t * ep_list[MAX_NODE_EPOINTS];
} zb_node_t;

zb_node_t node_table[MAX_NODES];
zb_epoint_t ep_table[ZB_EP_TABLE_SIZE];
zcl_cluster_t cls_table[ZB_CLS_TABLE_SIZE];

inline zb_node_t* ZB_Node_new(){
	int idx = _next_node_idx;
	if (idx < MAX_NODES)
	{
		memset(node_table[idx],0,sizeof(zb_node_t));
		_next_node_idx++;
		ERROR_CODE = 0;
	}
	else
	{
		ERROR_CODE = NO_MORE_NODES;
		return NULL;
	}
	return node_table[idx];
}

inline zb_epoint_t* ZB_Ep_new(){
	int idx = _next_ep_idx;
	if (idx < ZB_EP_TABLE_SIZE)
	{
		memset(ep_table[idx],0,sizeof(zb_epoint_t));
		_next_ep_idx++;
		ERROR_CODE = 0;
	}
	else
	{
		ERROR_CODE = NO_MORE_EP;
		return NULL;
	}
	return ep_table[idx];
}

inline zcl_cluster_t* ZB_Cluster_new(){
	int idx = _next_cluster_idx;
	if (idx < ZB_CLS_TABLE_SIZE)
	{
		memset(cls_table[idx],0,sizeof(zcl_cluster_t));
		_next_cluster_idx++;
		ERROR_CODE = 0;
	}
	else
	{
		ERROR_CODE = NO_MORE_CLS;
		return NULL;
	}
	return cls_table[idx];
}


#endif //ZB_NODE_DB_H defined


