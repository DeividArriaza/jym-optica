from odoo import models, fields, api


class OpticaConsulta(models.Model):
    _name = 'optica.consulta'
    _description = 'Consulta/Examen Visual'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'
    _rec_name = 'display_name'

    # Relación con paciente
    paciente_id = fields.Many2one(
        'optica.paciente',
        string='Paciente',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    # Datos heredados del paciente
    paciente_telefono = fields.Char(
        related='paciente_id.telefono',
        string='Teléfono'
    )
    paciente_edad = fields.Integer(
        related='paciente_id.edad',
        string='Edad'
    )

    # Datos de la consulta
    fecha = fields.Date(
        string='Fecha de Consulta',
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    optometrista_id = fields.Many2one(
        'res.users',
        string='Optometrista',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    motivo_consulta = fields.Text(string='Motivo de Consulta')

    # AGUDEZA VISUAL (AV)
    av_sl_od = fields.Char(string='AV/SL OD', help='Agudeza Visual Sin Lentes - Ojo Derecho')
    av_sl_oi = fields.Char(string='AV/SL OI', help='Agudeza Visual Sin Lentes - Ojo Izquierdo')
    av_cl_od = fields.Char(string='AV/CL OD', help='Agudeza Visual Con Lentes - Ojo Derecho')
    av_cl_oi = fields.Char(string='AV/CL OI', help='Agudeza Visual Con Lentes - Ojo Izquierdo')

    # LENSOMETRÍA
    lensometria_od = fields.Char(string='Lensometría OD')
    lensometria_oi = fields.Char(string='Lensometría OI')

    # RETINOSCOPÍA
    ret_od_esfera = fields.Char(string='Ret. Esfera OD')
    ret_od_cilindro = fields.Char(string='Ret. Cilindro OD')
    ret_od_eje = fields.Char(string='Ret. Eje OD')
    ret_oi_esfera = fields.Char(string='Ret. Esfera OI')
    ret_oi_cilindro = fields.Char(string='Ret. Cilindro OI')
    ret_oi_eje = fields.Char(string='Ret. Eje OI')

    # RX NUEVA (Graduación Final)
    rx_od_esfera = fields.Char(string='RX Esfera OD')
    rx_od_cilindro = fields.Char(string='RX Cilindro OD')
    rx_od_eje = fields.Char(string='RX Eje OD')
    rx_od_add = fields.Char(string='RX ADD OD')
    rx_oi_esfera = fields.Char(string='RX Esfera OI')
    rx_oi_cilindro = fields.Char(string='RX Cilindro OI')
    rx_oi_eje = fields.Char(string='RX Eje OI')
    rx_oi_add = fields.Char(string='RX ADD OI')

    # DIP
    dip_od = fields.Float(string='DIP OD', digits=(4, 2))
    dip_oi = fields.Float(string='DIP OI', digits=(4, 2))
    dip_total = fields.Float(string='DIP Total', digits=(4, 2))

    # PRESIÓN INTRAOCULAR
    presion_od = fields.Float(string='Presión OD', digits=(4, 2))
    presion_oi = fields.Float(string='Presión OI', digits=(4, 2))

    # OBSERVACIONES CLÍNICAS
    anexos_oculares = fields.Text(string='Anexos Oculares')
    fondo_ojo = fields.Text(string='Fondo de Ojo')
    diagnostico = fields.Text(string='Diagnóstico')
    observaciones = fields.Text(string='Observaciones')
    recomendaciones = fields.Text(string='Recomendaciones')

    # PRODUCTO/VENTA
    tipo_lente = fields.Selection([
        ('monofocal', 'Monofocal'),
        ('bifocal', 'Bifocal'),
        ('progresivo', 'Progresivo'),
        ('ocupacional', 'Ocupacional'),
        ('contacto', 'Lente de Contacto')
    ], string='Tipo de Lente')

    material_lente = fields.Selection([
        ('cr39', 'CR-39'),
        ('policarbonato', 'Policarbonato'),
        ('alto_indice', 'Alto Índice'),
        ('trivex', 'Trivex'),
        ('cristal', 'Cristal')
    ], string='Material del Lente')

    tratamientos_lente = fields.Selection([
        ('antireflejo', 'Antirreflejo'),
        ('fotocromatico', 'Fotocromático'),
        ('blue_block', 'Blue Block'),
        ('transitions', 'Transitions'),
        ('polarizado', 'Polarizado')
    ], string='Tratamiento del Lente')

    armazon_marca = fields.Char(string='Marca del Armazón')
    armazon_modelo = fields.Char(string='Modelo del Armazón')
    armazon_color = fields.Char(string='Color del Armazón')

    # Dibujos clínicos
    dibujo_ids = fields.One2many(
        'optica.dibujo.clinico',
        'consulta_id',
        string='Dibujos Clínicos'
    )

    proxima_cita_sugerida = fields.Date(string='Próxima Cita Sugerida')
    notas = fields.Text(string='Notas de Graduación')

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('paciente_id', 'fecha')
    def _compute_display_name(self):
        for record in self:
            if record.paciente_id and record.fecha:
                record.display_name = f"{record.paciente_id.name} - {record.fecha}"
            else:
                record.display_name = "Nueva Consulta"

    def action_crear_cita_seguimiento(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Cita de Seguimiento',
            'res_model': 'optica.cita',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_paciente_id': self.paciente_id.id,
                'default_motivo': 'Seguimiento de consulta del %s' % self.fecha,
                'default_fecha': self.proxima_cita_sugerida or fields.Date.today(),
            }
        }

    def action_agregar_dibujo(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agregar Dibujo Clínico',
            'res_model': 'optica.dibujo.clinico',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_consulta_id': self.id}
        }
