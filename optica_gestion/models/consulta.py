from odoo import models, fields, api


class OpticaConsulta(models.Model):
    _name = 'optica.consulta'
    _description = 'Consulta/Examen Visual'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'
    _rec_name = 'display_name'

    # Relación con contacto (paciente)
    partner_id = fields.Many2one(
        'res.partner',
        string='Paciente',
        required=True,
        ondelete='cascade',
        tracking=True,
        domain=[('is_optica_patient', '=', True)]
    )

    # Datos heredados del paciente (solo lectura)
    partner_telefono = fields.Char(
        related='partner_id.phone',
        string='Teléfono'
    )

    # Edad al momento de la consulta (editable, independiente)
    edad_consulta = fields.Integer(
        string='Edad',
        help='Edad del paciente al momento de la consulta'
    )

    # Datos de la consulta
    fecha = fields.Date(
        string='Fecha de Consulta',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    fecha_formateada = fields.Char(
        string='Fecha de Consulta',
        compute='_compute_fecha_formateada',
        store=True
    )

    optometrista_id = fields.Many2one(
        'res.users',
        string='Optometrista',
        default=lambda self: self.env.user,
        tracking=True
    )

    motivo_consulta = fields.Text(string='Motivo de Consulta')

    @api.depends('fecha')
    def _compute_fecha_formateada(self):
        for record in self:
            if record.fecha:
                record.fecha_formateada = record.fecha.strftime('%d/%m/%Y')
            else:
                record.fecha_formateada = ''

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Al seleccionar paciente, auto-completar edad"""
        if self.partner_id and self.partner_id.edad:
            self.edad_consulta = self.partner_id.edad

    # ==================== AGUDEZA VISUAL (AV) ====================
    # Sin Lentes (SL)
    av_sl_od = fields.Char(string='AV/SL OD')
    av_sl_oi = fields.Char(string='AV/SL OI')
    # Con Lentes (CL)
    av_cl_od = fields.Char(string='AV/CL OD')
    av_cl_oi = fields.Char(string='AV/CL OI')

    # ==================== LENSOMETRÍA ====================
    # Ojo Derecho
    lens_od_esfera = fields.Char(string='Esfera')
    lens_od_cilindro = fields.Char(string='Cilindro')
    lens_od_eje = fields.Char(string='Eje')
    lens_od_add = fields.Char(string='ADD')
    # Ojo Izquierdo
    lens_oi_esfera = fields.Char(string='Esfera')
    lens_oi_cilindro = fields.Char(string='Cilindro')
    lens_oi_eje = fields.Char(string='Eje')
    lens_oi_add = fields.Char(string='ADD')

    # ==================== RETINOSCOPÍA ====================
    # Ojo Derecho
    ret_od_esfera = fields.Char(string='Esfera')
    ret_od_cilindro = fields.Char(string='Cilindro')
    ret_od_eje = fields.Char(string='Eje')
    ret_od_av = fields.Char(string='AV')
    # Ojo Izquierdo
    ret_oi_esfera = fields.Char(string='Esfera')
    ret_oi_cilindro = fields.Char(string='Cilindro')
    ret_oi_eje = fields.Char(string='Eje')
    ret_oi_av = fields.Char(string='AV')

    # ==================== RX NUEVA (Graduación Final) ====================
    # Ojo Derecho
    rx_od_esfera = fields.Char(string='Esfera')
    rx_od_cilindro = fields.Char(string='Cilindro')
    rx_od_eje = fields.Char(string='Eje')
    rx_od_add = fields.Char(string='ADD')
    rx_od_av = fields.Char(string='AV')
    # Ojo Izquierdo
    rx_oi_esfera = fields.Char(string='Esfera')
    rx_oi_cilindro = fields.Char(string='Cilindro')
    rx_oi_eje = fields.Char(string='Eje')
    rx_oi_add = fields.Char(string='ADD')
    rx_oi_av = fields.Char(string='AV')

    # ==================== OBSERVACIONES RX ====================
    rx_observaciones = fields.Text(string='RX')
    
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
    observaciones = fields.Text(string='Observaciones Generales')
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

    @api.depends('partner_id', 'fecha')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.fecha:
                record.display_name = f"{record.partner_id.name} - {record.fecha}"
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
                'default_partner_id': self.partner_id.id,
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

    def action_eliminar_consulta(self):
        """Eliminar consulta con confirmación"""
        self.ensure_one()
        self.unlink()
        return True
