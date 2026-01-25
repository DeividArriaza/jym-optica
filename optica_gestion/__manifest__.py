{
    'name': 'Gestión de Óptica',
    'version': '19.0.2.0.0',
    'category': 'Healthcare',
    'summary': 'Sistema de gestión de pacientes y consultas para ópticas',
    'description': """
        Módulo para gestión integral de ópticas:
        - Pacientes integrados con Contactos de Odoo
        - Historial de consultas con graduaciones
        - Agenda de citas integrada con calendario
        - Compatible con Ventas, Facturación, CRM
    """,
    'author': 'Adroc',
    'depends': ['base', 'mail', 'calendar', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_views.xml',
        'views/consulta_views.xml',
        'views/cita_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
