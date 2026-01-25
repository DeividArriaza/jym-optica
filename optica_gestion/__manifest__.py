{
    'name': 'Gestión de Óptica',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Sistema de gestión de pacientes y citas para ópticas',
    'description': """
        Módulo para gestión integral de ópticas:
        - Registro y expedientes de pacientes
        - Historial de consultas con graduaciones
        - Agenda de citas integrada con calendario
        - Control de lista negra
    """,
    'author': 'Adroc',
    'depends': ['base', 'mail', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'views/paciente_views.xml',
        'views/consulta_views.xml',
        'views/cita_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
