#ifndef _DFD_FRUEEPROM_H_
#define _DFD_FRUEEPROM_H_

/* Per IPMI v2.0 FRU specification */
typedef struct fru_common_header_s
{
    uint8_t fixed;
    uint8_t internal_offset;
    uint8_t chassis_offset;
    uint8_t board_offset;
    uint8_t product_offset;
    uint8_t multi_offset;
    uint8_t pad;
    uint8_t crc;
}__attribute__((packed)) fru_common_header_t;

/* first byte in header is 1h per IPMI V2 spec. */

#define IPMI_FRU_HDR_BYTE_ZERO   1
#define IPMI_EIGHT_BYTES         8
#define IPMI_FRU_PRODUCT_AREA_MIN_LEN       (7)
#define IPMI_FRU_BOARD_AREA_MIN_LEN         (5)

#define IPMI_FRU_AREA_TYPE_LENGTH_FIELD_MAX            512
#define IPMI_FRU_BOARD_INFO_MFG_TIME_LENGTH            3
#define IPMI_FRU_SENTINEL_VALUE                        0xC1
#define IPMI_FRU_TYPE_LENGTH_TYPE_CODE_MASK            0xC0
#define IPMI_FRU_TYPE_LENGTH_TYPE_CODE_SHIFT           0x06
#define IPMI_FRU_TYPE_LENGTH_NUMBER_OF_DATA_BYTES_MASK 0x3F
#define IPMI_FRU_TYPE_LENGTH_TYPE_CODE_LANGUAGE_CODE   0x03

struct ipmi_fru_field
{
  uint8_t type_length_field[IPMI_FRU_AREA_TYPE_LENGTH_FIELD_MAX];
  /* store length of data stored in buffer */
  unsigned int type_length_field_length;
};

typedef struct ipmi_fru_field ipmi_fru_field_t;

typedef struct ipmi_product_info_s {
    uint8_t *language_code;
    ipmi_fru_field_t *product_manufacturer_name;
    ipmi_fru_field_t *product_name;
    ipmi_fru_field_t *product_part_model_number;
    ipmi_fru_field_t *product_version;
    ipmi_fru_field_t *product_serial_number;
    ipmi_fru_field_t *product_asset_tag;
    ipmi_fru_field_t *product_fru_file_id;
    ipmi_fru_field_t *product_custom_fields;
    ipmi_fru_field_t *product_type_fields;
}ipmi_product_info_t;

typedef struct ipmi_board_info_s {
    uint8_t *language_code;
    uint8_t *mfg_time;
    ipmi_fru_field_t *board_manufacturer;
    ipmi_fru_field_t *board_product_name;
    ipmi_fru_field_t *board_serial_number;
    ipmi_fru_field_t *board_part_number;
    ipmi_fru_field_t *board_fru_file_id;
    ipmi_fru_field_t *board_custom_fields;  /*hw version */
}ipmi_board_info_t;

int dfd_get_fru_data(int bus, int dev_addr, int type, uint8_t *buf, uint32_t buf_len, const char *sysfs_name);

int dfd_get_fru_board_data(int bus, int dev_addr, int type, uint8_t *buf, uint32_t buf_len, const char *sysfs_name);

#endif /* endif _DFD_FRUEEPROM_H_ */
