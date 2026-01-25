from odoo import models, fields


class OpticaDibujoClinico(models.Model):
    _name = 'optica.dibujo.clinico'
    _description = 'Dibujo Clínico'

    consulta_id = fields.Many2one(
        'optica.consulta',
        string='Consulta',
        required=True,
        ondelete='cascade'
    )
    
    nombre = fields.Char(
        string='Nombre',
        required=True
    )
    
    tipo = fields.Selection([
        ('ojo_derecho', 'Ojo Derecho'),
        ('ojo_izquierdo', 'Ojo Izquierdo'),
        ('ambos', 'Ambos Ojos'),
        ('otro', 'Otro')
    ], string='Tipo', default='otro')
    
    imagen = fields.Binary(
        string='Imagen',
        attachment=True
    )
    
    descripcion = fields.Text(
        string='Descripción'
    )
