# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


GLIB_CDEF = """
typedef char gchar;
typedef const void * gconstpointer;
typedef double gdouble;
typedef float gfloat;
typedef int gboolean;
typedef int16_t gint16;
typedef int32_t gint32;
typedef int64_t gint64;
typedef int8_t gint8;
typedef int gint;
typedef long glong;
typedef short gshort;
typedef size_t gsize;
typedef uint16_t guint16;
typedef uint32_t guint32;
typedef uint64_t guint64;
typedef uint8_t guint8;
typedef unsigned int guint;
typedef unsigned long gulong;
typedef unsigned short gushort;
typedef intptr_t gpointer;
typedef signed long gssize;

// utility functions

gpointer g_malloc0(gsize);
void g_free(gpointer);
gpointer g_try_malloc0(gsize);
gchar* g_strdup(gchar*);
gpointer g_memdup(gconstpointer mem, guint byte_size);

typedef void (*GFunc)(gpointer data, gpointer user_data);

// GQuark

typedef guint32 GQuark;
GQuark g_quark_from_string(gchar*);
gchar* g_quark_to_string(GQuark);
GQuark g_quark_try_string(gchar*);

// GError

typedef struct {
  GQuark    domain;
  gint      code;
  gchar     *message;
} GError;

void g_error_free (GError *error);
GError* g_error_copy(const GError *error);
GError* g_error_new(GQuark domain, gint code, const gchar *format, ...);

// GMappedFile

typedef struct _GMappedFile GMappedFile;

GMappedFile* g_mapped_file_new(const gchar *filename,
                               gboolean writable,
                               GError **error);
GMappedFile* g_mapped_file_ref(GMappedFile *file);
void g_mapped_file_unref(GMappedFile *file);
gsize g_mapped_file_get_length(GMappedFile *file);
gchar* g_mapped_file_get_contents(GMappedFile *file);

// GOptionGroup

typedef struct _GOptionGroup GOptionGroup;
void g_option_group_free(GOptionGroup *group);

// GSList

typedef struct _GSList {
  gpointer data;
  struct _GSList *next;
} GSList;

GSList* g_slist_alloc(void);
GSList* g_slist_append(GSList *list, gpointer data);
void g_slist_free(GSList *list);
guint g_slist_length(GSList *list);
void g_slist_foreach (GSList *list, GFunc func, gpointer user_data);

// GList

typedef struct _GList {
  gpointer data;
  struct _GList *next;
  struct _GList *prev;
} GList;

void g_list_free(GList *list);
"""
