# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import _fixup_cdef_enums


GI_TYPES_CDEF = """
typedef struct _GIBaseInfoStub GIBaseInfo;
typedef GIBaseInfo GICallableInfo;
typedef GIBaseInfo GIFunctionInfo;
typedef GIBaseInfo GICallbackInfo;
typedef GIBaseInfo GIRegisteredTypeInfo;
typedef GIBaseInfo GIStructInfo;
typedef GIBaseInfo GIUnionInfo;
typedef GIBaseInfo GIEnumInfo;
typedef GIBaseInfo GIObjectInfo;
typedef GIBaseInfo GIInterfaceInfo;
typedef GIBaseInfo GIConstantInfo;
typedef GIBaseInfo GIValueInfo;
typedef GIBaseInfo GISignalInfo;
typedef GIBaseInfo GIVFuncInfo;
typedef GIBaseInfo GIPropertyInfo;
typedef GIBaseInfo GIFieldInfo;
typedef GIBaseInfo GIArgInfo;
typedef GIBaseInfo GITypeInfo;

typedef union
{
  gboolean v_boolean;
  gint8    v_int8;
  guint8   v_uint8;
  gint16   v_int16;
  guint16  v_uint16;
  gint32   v_int32;
  guint32  v_uint32;
  gint64   v_int64;
  guint64  v_uint64;
  gfloat   v_float;
  gdouble  v_double;
  gshort   v_short;
  gushort  v_ushort;
  gint     v_int;
  guint    v_uint;
  glong    v_long;
  gulong   v_ulong;
  gssize   v_ssize;
  gsize    v_size;
  gchar *  v_string;
  gpointer v_pointer;
} GIArgument;

typedef enum
{
  GI_INFO_TYPE_INVALID,
  GI_INFO_TYPE_FUNCTION,
  GI_INFO_TYPE_CALLBACK,
  GI_INFO_TYPE_STRUCT,
  GI_INFO_TYPE_BOXED,
  GI_INFO_TYPE_ENUM,
  GI_INFO_TYPE_FLAGS,
  GI_INFO_TYPE_OBJECT,
  GI_INFO_TYPE_INTERFACE,
  GI_INFO_TYPE_CONSTANT,
  GI_INFO_TYPE_INVALID_0,
  GI_INFO_TYPE_UNION,
  GI_INFO_TYPE_VALUE,
  GI_INFO_TYPE_SIGNAL,
  GI_INFO_TYPE_VFUNC,
  GI_INFO_TYPE_PROPERTY,
  GI_INFO_TYPE_FIELD,
  GI_INFO_TYPE_ARG,
  GI_INFO_TYPE_TYPE,
  GI_INFO_TYPE_UNRESOLVED
} GIInfoType;

typedef enum {
  GI_TRANSFER_NOTHING,
  GI_TRANSFER_CONTAINER,
  GI_TRANSFER_EVERYTHING
} GITransfer;

typedef enum  {
  GI_DIRECTION_IN,
  GI_DIRECTION_OUT,
  GI_DIRECTION_INOUT
} GIDirection;

typedef enum {
  GI_SCOPE_TYPE_INVALID,
  GI_SCOPE_TYPE_CALL,
  GI_SCOPE_TYPE_ASYNC,
  GI_SCOPE_TYPE_NOTIFIED
} GIScopeType;

typedef enum {
  GI_TYPE_TAG_VOID      =  0,
  GI_TYPE_TAG_BOOLEAN   =  1,
  GI_TYPE_TAG_INT8      =  2,
  GI_TYPE_TAG_UINT8     =  3,
  GI_TYPE_TAG_INT16     =  4,
  GI_TYPE_TAG_UINT16    =  5,
  GI_TYPE_TAG_INT32     =  6,
  GI_TYPE_TAG_UINT32    =  7,
  GI_TYPE_TAG_INT64     =  8,
  GI_TYPE_TAG_UINT64    =  9,
  GI_TYPE_TAG_FLOAT     = 10,
  GI_TYPE_TAG_DOUBLE    = 11,
  GI_TYPE_TAG_GTYPE     = 12,
  GI_TYPE_TAG_UTF8      = 13,
  GI_TYPE_TAG_FILENAME  = 14,
  GI_TYPE_TAG_ARRAY     = 15,
  GI_TYPE_TAG_INTERFACE = 16,
  GI_TYPE_TAG_GLIST     = 17,
  GI_TYPE_TAG_GSLIST    = 18,
  GI_TYPE_TAG_GHASH     = 19,
  GI_TYPE_TAG_ERROR     = 20,
  GI_TYPE_TAG_UNICHAR   = 21
} GITypeTag;

typedef enum {
  GI_ARRAY_TYPE_C,
  GI_ARRAY_TYPE_ARRAY,
  GI_ARRAY_TYPE_PTR_ARRAY,
  GI_ARRAY_TYPE_BYTE_ARRAY
} GIArrayType;

typedef enum
{
  GI_FIELD_IS_READABLE = 1 << 0,
  GI_FIELD_IS_WRITABLE = 1 << 1
} GIFieldInfoFlags;

typedef enum
{
  GI_VFUNC_MUST_CHAIN_UP     = 1 << 0,
  GI_VFUNC_MUST_OVERRIDE     = 1 << 1,
  GI_VFUNC_MUST_NOT_OVERRIDE = 1 << 2,
  GI_VFUNC_THROWS =            1 << 3
} GIVFuncInfoFlags;

typedef enum
{
  GI_FUNCTION_IS_METHOD      = 1 << 0,
  GI_FUNCTION_IS_CONSTRUCTOR = 1 << 1,
  GI_FUNCTION_IS_GETTER      = 1 << 2,
  GI_FUNCTION_IS_SETTER      = 1 << 3,
  GI_FUNCTION_WRAPS_VFUNC    = 1 << 4,
  GI_FUNCTION_THROWS         = 1 << 5
} GIFunctionInfoFlags;

typedef enum {
  G_INVOKE_ERROR_FAILED,
  G_INVOKE_ERROR_SYMBOL_NOT_FOUND,
  G_INVOKE_ERROR_ARGUMENT_MISMATCH
} GInvokeError;
"""

GI_TYPELIB_CDEF = """
typedef struct _GITypelib GITypelib;

GITypelib *    g_typelib_new_from_memory       (guint8        *memory,
                                               gsize          len,
                           GError       **error);
GITypelib *    g_typelib_new_from_const_memory (const guint8  *memory,
                                               gsize          len,
                           GError       **error);
GITypelib *    g_typelib_new_from_mapped_file  (GMappedFile   *mfile,
                           GError       **error);
void          g_typelib_free                  (GITypelib     *typelib);

gboolean      g_typelib_symbol                (GITypelib     *typelib,
                                               const gchar  *symbol_name,
                                               gpointer     *symbol);
const gchar * g_typelib_get_namespace         (GITypelib     *typelib);
"""

GI_REPOSITORY_CDEF = """
typedef struct _GIRepository         GIRepository;

typedef enum
{
  G_IREPOSITORY_LOAD_FLAG_LAZY = 1 << 0
} GIRepositoryLoadFlags;

GType         g_irepository_get_type      (void);
GIRepository *g_irepository_get_default   (void);
void          g_irepository_prepend_search_path (const char *directory);
void          g_irepository_prepend_library_path (const char *directory);
GSList *      g_irepository_get_search_path     (void);
const char *  g_irepository_load_typelib  (GIRepository *repository,
                       GITypelib     *typelib,
                       GIRepositoryLoadFlags flags,
                       GError      **error);
gboolean      g_irepository_is_registered (GIRepository *repository,
                       const gchar  *namespace_,
                       const gchar  *version);
GIBaseInfo *  g_irepository_find_by_name  (GIRepository *repository,
                       const gchar  *namespace_,
                       const gchar  *name);
GList *       g_irepository_enumerate_versions (GIRepository *repository,
                            const gchar  *namespace_);
GITypelib *    g_irepository_require       (GIRepository *repository,
                       const gchar  *namespace_,
                       const gchar  *version,
                       GIRepositoryLoadFlags flags,
                       GError      **error);
GITypelib *    g_irepository_require_private (GIRepository  *repository,
                         const gchar   *typelib_dir,
                         const gchar   *namespace_,
                         const gchar   *version,
                         GIRepositoryLoadFlags flags,
                         GError       **error);
gchar      ** g_irepository_get_dependencies (GIRepository *repository,
                          const gchar  *namespace_);
gchar      ** g_irepository_get_immediate_dependencies (GIRepository *repository,
                                          const char   *namespace);
gchar      ** g_irepository_get_loaded_namespaces (GIRepository *repository);
GIBaseInfo *  g_irepository_find_by_gtype (GIRepository *repository,
                       GType         gtype);
gint          g_irepository_get_n_infos   (GIRepository *repository,
                       const gchar  *namespace_);
GIBaseInfo *  g_irepository_get_info      (GIRepository *repository,
                       const gchar  *namespace_,
                       gint          index);
GIEnumInfo *  g_irepository_find_by_error_domain (GIRepository *repository,
                          GQuark        domain);
const gchar * g_irepository_get_typelib_path   (GIRepository *repository,
                        const gchar  *namespace_);
const gchar * g_irepository_get_shared_library (GIRepository *repository,
                        const gchar  *namespace_);
const gchar * g_irepository_get_c_prefix (GIRepository *repository,
                                          const gchar  *namespace_);
const gchar * g_irepository_get_version (GIRepository *repository,
                     const gchar  *namespace_);

GOptionGroup * g_irepository_get_option_group (void);

gboolean       g_irepository_dump  (const char *arg, GError **error);

typedef enum
{
  G_IREPOSITORY_ERROR_TYPELIB_NOT_FOUND,
  G_IREPOSITORY_ERROR_NAMESPACE_MISMATCH,
  G_IREPOSITORY_ERROR_NAMESPACE_VERSION_CONFLICT,
  G_IREPOSITORY_ERROR_LIBRARY_NOT_FOUND
} GIRepositoryError;

GQuark g_irepository_error_quark (void);
"""

GI_ENUMEINFO_CDEF = """
gint           g_enum_info_get_n_values      (GIEnumInfo  *info);
GIValueInfo  * g_enum_info_get_value         (GIEnumInfo  *info,
                          gint         n);
gint              g_enum_info_get_n_methods     (GIEnumInfo  *info);
GIFunctionInfo  * g_enum_info_get_method        (GIEnumInfo  *info,
                         gint         n);
GITypeTag      g_enum_info_get_storage_type  (GIEnumInfo  *info);
const gchar *  g_enum_info_get_error_domain  (GIEnumInfo  *info);

gint64         g_value_info_get_value        (GIValueInfo *info);

"""

GI_BASEINFO_CDEF = """
typedef struct {
  gpointer data;
  gpointer data2;
  gpointer data3;
  gpointer data4;
} GIAttributeIter;

GIBaseInfo *        g_base_info_ref                 (GIBaseInfo *info);
void                g_base_info_unref               (GIBaseInfo *info);
GIInfoType          g_base_info_get_type            (GIBaseInfo *info);
const gchar *       g_base_info_get_name            (GIBaseInfo *info);
const gchar *       g_base_info_get_namespace       (GIBaseInfo *info);
gboolean            g_base_info_is_deprecated       (GIBaseInfo *info);
const gchar *       g_base_info_get_attribute       (GIBaseInfo *info,
                                                     const gchar *name);
gboolean            g_base_info_iterate_attributes  (GIBaseInfo *info,
                                                     GIAttributeIter *iterator,
                                                     char **name,
                                                     char **value);
GIBaseInfo *        g_base_info_get_container       (GIBaseInfo *info);
GITypelib *         g_base_info_get_typelib         (GIBaseInfo *info);
gboolean            g_base_info_equal               (GIBaseInfo *info1,
                                                     GIBaseInfo *info2);
"""

GI_TYPEINFO_CDEF = """
const gchar*           g_type_tag_to_string            (GITypeTag   type);
const gchar*           g_info_type_to_string           (GIInfoType  type);
gboolean               g_type_info_is_pointer          (GITypeInfo *info);
GITypeTag              g_type_info_get_tag             (GITypeInfo *info);
GITypeInfo *           g_type_info_get_param_type      (GITypeInfo *info,
                                                        gint       n);
GIBaseInfo *           g_type_info_get_interface       (GITypeInfo *info);
gint                   g_type_info_get_array_length    (GITypeInfo *info);
gint                   g_type_info_get_array_fixed_size(GITypeInfo *info);
gboolean               g_type_info_is_zero_terminated  (GITypeInfo *info);
GIArrayType            g_type_info_get_array_type      (GITypeInfo *info);
"""

GI_ARGINFO_CDEF = """
GIDirection            g_arg_info_get_direction          (GIArgInfo *info);
gboolean               g_arg_info_is_return_value        (GIArgInfo *info);
gboolean               g_arg_info_is_optional            (GIArgInfo *info);
gboolean               g_arg_info_is_caller_allocates    (GIArgInfo *info);
gboolean               g_arg_info_may_be_null            (GIArgInfo *info);
gboolean               g_arg_info_is_skip                (GIArgInfo *info);
GITransfer             g_arg_info_get_ownership_transfer (GIArgInfo *info);
GIScopeType            g_arg_info_get_scope              (GIArgInfo *info);
gint                   g_arg_info_get_closure            (GIArgInfo *info);
gint                   g_arg_info_get_destroy            (GIArgInfo *info);
GITypeInfo *           g_arg_info_get_type               (GIArgInfo *info);
void                   g_arg_info_load_type              (GIArgInfo *info,
                                                          GITypeInfo *type);
"""

GI_CONSTINFO_CDEF = """
GITypeInfo * g_constant_info_get_type (GIConstantInfo *info);
void         g_constant_info_free_value(GIConstantInfo *info,
                                        GIArgument      *value);
gint         g_constant_info_get_value(GIConstantInfo *info,
                                       GIArgument      *value);
"""


GI_REGIST_CDEF = """
const gchar *       g_registered_type_info_get_type_name
                                                        (GIRegisteredTypeInfo *info);
const gchar *       g_registered_type_info_get_type_init
                                                        (GIRegisteredTypeInfo *info);
GType               g_registered_type_info_get_g_type   (GIRegisteredTypeInfo *info);
"""


GI_FIELD_CDEF = """
GIFieldInfoFlags    g_field_info_get_flags              (GIFieldInfo *info);
gint                g_field_info_get_size               (GIFieldInfo *info);
gint                g_field_info_get_offset             (GIFieldInfo *info);
GITypeInfo *        g_field_info_get_type               (GIFieldInfo *info);
gboolean            g_field_info_get_field              (GIFieldInfo *field_info,
                                                         gpointer mem,
                                                         GIArgument *value);
gboolean            g_field_info_set_field              (GIFieldInfo *field_info,
                                                         gpointer mem,
                                                         const GIArgument *value);
"""


GI_CALL_CDEF = """
GITypeInfo *        g_callable_info_get_return_type     (GICallableInfo *info);
GITransfer          g_callable_info_get_caller_owns     (GICallableInfo *info);
gboolean            g_callable_info_may_return_null     (GICallableInfo *info);
const gchar *       g_callable_info_get_return_attribute
                                                        (GICallableInfo *info,
                                                         const gchar *name);
gboolean            g_callable_info_iterate_return_attributes
                                                        (GICallableInfo *info,
                                                         GIAttributeIter *iterator,
                                                         char **name,
                                                         char **value);
gint                g_callable_info_get_n_args          (GICallableInfo *info);
GIArgInfo *         g_callable_info_get_arg             (GICallableInfo *info,
                                                         gint n);
void                g_callable_info_load_arg            (GICallableInfo *info,
                                                         gint n,
                                                         GIArgInfo *arg);
void                g_callable_info_load_return_type    (GICallableInfo *info,
                                                         GITypeInfo *type);
gboolean            g_callable_info_can_throw_gerror    (GICallableInfo *info);
gboolean            g_callable_info_skip_return         (GICallableInfo *info);
"""


GI_ENUM_CDEF = """
gint                g_enum_info_get_n_values            (GIEnumInfo *info);
GIValueInfo *       g_enum_info_get_value               (GIEnumInfo *info,
                                                         gint n);
gint                g_enum_info_get_n_methods           (GIEnumInfo *info);
GIFunctionInfo *    g_enum_info_get_method              (GIEnumInfo *info,
                                                         gint n);
GITypeTag           g_enum_info_get_storage_type        (GIEnumInfo *info);
const gchar *       g_enum_info_get_error_domain        (GIEnumInfo *info);
gint64              g_value_info_get_value              (GIValueInfo *info);
"""


GI_FUNC_CDEF = """
const gchar *       g_function_info_get_symbol          (GIFunctionInfo *info);
GIFunctionInfoFlags g_function_info_get_flags           (GIFunctionInfo *info);
GIPropertyInfo *    g_function_info_get_property        (GIFunctionInfo *info);
GIVFuncInfo *       g_function_info_get_vfunc           (GIFunctionInfo *info);
gboolean            g_function_info_invoke              (GIFunctionInfo *info,
                                                         const GIArgument *in_args,
                                                         int n_in_args,
                                                         const GIArgument *out_args,
                                                         int n_out_args,
                                                         GIArgument *return_value,
                                                         GError **error);
"""


GI_UNION_CDEF = """
gint                g_union_info_get_n_fields           (GIUnionInfo *info);
GIFieldInfo *       g_union_info_get_field              (GIUnionInfo *info,
                                                         gint n);
gint                g_union_info_get_n_methods          (GIUnionInfo *info);
GIFunctionInfo *    g_union_info_get_method             (GIUnionInfo *info,
                                                         gint n);
gboolean            g_union_info_is_discriminated       (GIUnionInfo *info);
gint                g_union_info_get_discriminator_offset
                                                        (GIUnionInfo *info);
GITypeInfo *        g_union_info_get_discriminator_type (GIUnionInfo *info);
GIConstantInfo *    g_union_info_get_discriminator      (GIUnionInfo *info,
                                                         gint n);
GIFunctionInfo *    g_union_info_find_method            (GIUnionInfo *info,
                                                         const gchar *name);
gsize               g_union_info_get_size               (GIUnionInfo *info);
gsize               g_union_info_get_alignment          (GIUnionInfo *info);
"""


GI_OBJECT_CDEF = """
typedef void * (*GIObjectInfoRefFunction) (void *object);
typedef void   (*GIObjectInfoUnrefFunction) (void *object);
typedef void   (*GIObjectInfoSetValueFunction) (GValue *value, void *object);
typedef void * (*GIObjectInfoGetValueFunction) (const GValue *value);

const gchar *       g_object_info_get_type_name         (GIObjectInfo *info);
const gchar *       g_object_info_get_type_init         (GIObjectInfo *info);
gboolean            g_object_info_get_abstract          (GIObjectInfo *info);
gboolean            g_object_info_get_fundamental       (GIObjectInfo *info);
GIObjectInfo *      g_object_info_get_parent            (GIObjectInfo *info);
gint                g_object_info_get_n_interfaces      (GIObjectInfo *info);
GIInterfaceInfo *   g_object_info_get_interface         (GIObjectInfo *info,
                                                         gint n);
gint                g_object_info_get_n_fields          (GIObjectInfo *info);
GIFieldInfo *       g_object_info_get_field             (GIObjectInfo *info,
                                                         gint n);
gint                g_object_info_get_n_properties      (GIObjectInfo *info);
GIPropertyInfo *    g_object_info_get_property          (GIObjectInfo *info,
                                                         gint n);
gint                g_object_info_get_n_methods         (GIObjectInfo *info);
GIFunctionInfo *    g_object_info_get_method            (GIObjectInfo *info,
                                                         gint n);
GIFunctionInfo *    g_object_info_find_method           (GIObjectInfo *info,
                                                         const gchar *name);
gint                g_object_info_get_n_signals         (GIObjectInfo *info);
GISignalInfo *      g_object_info_get_signal            (GIObjectInfo *info,
                                                         gint n);
gint                g_object_info_get_n_vfuncs          (GIObjectInfo *info);
GIVFuncInfo *       g_object_info_get_vfunc             (GIObjectInfo *info,
                                                         gint n);
gint                g_object_info_get_n_constants       (GIObjectInfo *info);
GIConstantInfo *    g_object_info_get_constant          (GIObjectInfo *info,
                                                         gint n);
GIStructInfo *      g_object_info_get_class_struct      (GIObjectInfo *info);
GIVFuncInfo *       g_object_info_find_vfunc            (GIObjectInfo *info,
                                                         const gchar *name);
const char *        g_object_info_get_unref_function    (GIObjectInfo *info);
GIObjectInfoUnrefFunction g_object_info_get_unref_function_pointer
                                                        (GIObjectInfo *info);
const char *        g_object_info_get_ref_function      (GIObjectInfo *info);
GIObjectInfoRefFunction g_object_info_get_ref_function_pointer
                                                        (GIObjectInfo *info);
const char *        g_object_info_get_set_value_function
                                                        (GIObjectInfo *info);
GIObjectInfoSetValueFunction g_object_info_get_set_value_function_pointer
                                                        (GIObjectInfo *info);
const char *        g_object_info_get_get_value_function
                                                        (GIObjectInfo *info);
GIObjectInfoGetValueFunction g_object_info_get_get_value_function_pointer
                                                        (GIObjectInfo *info);
"""


GI_INTERFACE_CDEF = """
gint             g_interface_info_get_n_prerequisites (GIInterfaceInfo *info);
GIBaseInfo *     g_interface_info_get_prerequisite    (GIInterfaceInfo *info,
                                                       gint             n);
gint             g_interface_info_get_n_properties    (GIInterfaceInfo *info);
GIPropertyInfo * g_interface_info_get_property        (GIInterfaceInfo *info,
                                                       gint             n);
gint             g_interface_info_get_n_methods       (GIInterfaceInfo *info);
GIFunctionInfo * g_interface_info_get_method          (GIInterfaceInfo *info,
                                                       gint             n);
GIFunctionInfo * g_interface_info_find_method         (GIInterfaceInfo *info,
                                                       const gchar     *name);
gint             g_interface_info_get_n_signals       (GIInterfaceInfo *info);
GISignalInfo *   g_interface_info_get_signal          (GIInterfaceInfo *info,
                                                       gint             n);
GISignalInfo *   g_interface_info_find_signal         (GIInterfaceInfo *info,
                                                       const gchar  *name);
gint             g_interface_info_get_n_vfuncs        (GIInterfaceInfo *info);
GIVFuncInfo *    g_interface_info_get_vfunc           (GIInterfaceInfo *info,
                                                       gint             n);
GIVFuncInfo *    g_interface_info_find_vfunc          (GIInterfaceInfo *info,
                                                       const gchar     *name);
gint             g_interface_info_get_n_constants     (GIInterfaceInfo *info);
GIConstantInfo * g_interface_info_get_constant        (GIInterfaceInfo *info,
                                                       gint             n);
GIStructInfo *   g_interface_info_get_iface_struct    (GIInterfaceInfo *info);
"""


GI_STRUCT_CDEF = """
gint                g_struct_info_get_n_fields          (GIStructInfo *info);
GIFieldInfo *       g_struct_info_get_field             (GIStructInfo *info,
                                                         gint n);
gint                g_struct_info_get_n_methods         (GIStructInfo *info);
GIFunctionInfo *    g_struct_info_get_method            (GIStructInfo *info,
                                                         gint n);
GIFunctionInfo *    g_struct_info_find_method           (GIStructInfo *info,
                                                         const gchar *name);
gsize               g_struct_info_get_size              (GIStructInfo *info);
gsize               g_struct_info_get_alignment         (GIStructInfo *info);
gboolean            g_struct_info_is_gtype_struct       (GIStructInfo *info);
gboolean            g_struct_info_is_foreign            (GIStructInfo *info);
"""


GI_SIGNAL_DEF = """
GSignalFlags  g_signal_info_get_flags         (GISignalInfo *info);
GIVFuncInfo * g_signal_info_get_class_closure (GISignalInfo *info);
gboolean      g_signal_info_true_stops_emit   (GISignalInfo *info);
"""


GI_VFUNC_CDEF = """
GIVFuncInfoFlags  g_vfunc_info_get_flags   (GIVFuncInfo *info);
gint              g_vfunc_info_get_offset  (GIVFuncInfo *info);
GISignalInfo *    g_vfunc_info_get_signal  (GIVFuncInfo *info);
GIFunctionInfo *  g_vfunc_info_get_invoker (GIVFuncInfo *info);
gpointer          g_vfunc_info_get_address (GIVFuncInfo *info,
                                            GType        implementor_gtype,
                                            GError     **error);
"""


GI_PROP_CDEF = """
GParamFlags  g_property_info_get_flags (GIPropertyInfo *info);
GITypeInfo * g_property_info_get_type  (GIPropertyInfo *info);
GITransfer   g_property_info_get_ownership_transfer (GIPropertyInfo *info);
"""


GIR_CDEF = "".join([
    _fixup_cdef_enums(GI_TYPES_CDEF),
    GI_TYPELIB_CDEF,
    GI_BASEINFO_CDEF,
    _fixup_cdef_enums(GI_REPOSITORY_CDEF),
    GI_ARGINFO_CDEF,
    GI_CONSTINFO_CDEF,
    GI_REGIST_CDEF,
    GI_FIELD_CDEF,
    GI_CALL_CDEF,
    GI_VFUNC_CDEF,
    GI_ENUM_CDEF,
    GI_FUNC_CDEF,
    GI_UNION_CDEF,
    GI_OBJECT_CDEF,
    GI_INTERFACE_CDEF,
    GI_STRUCT_CDEF,
    GI_SIGNAL_DEF,
    GI_TYPEINFO_CDEF,
    GI_PROP_CDEF,
])
