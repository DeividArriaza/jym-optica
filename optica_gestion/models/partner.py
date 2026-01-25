from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Identificar como paciente de óptica
    is_optica_patient = fields.Boolean(
        string='Es Paciente de Óptica',
        default=False
    )

    # Número de ficha
    ficha_numero = fields.Char(
        string='Ficha No.',
        readonly=True,
        copy=False
    )

    # Datos adicionales del paciente
    fecha_nacimiento = fields.Date(
        string='Fecha de Nacimiento'
    )
    edad = fields.Integer(
        string='Edad',
        compute='_compute_edad',
        store=True
    )
    ocupacion = fields.Char(
        string='Ocupación'
    )
    referencia = fields.Char(
        string='Referencia',
        help='¿Cómo se enteró de nosotros?'
    )

    # Preguntas de la ficha
    evaluacion_visual_previa = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No')
    ], string='¿Evaluación Visual Previa?', default='no')

    fecha_ultima_evaluacion = fields.Date(
        string='Fecha Última Evaluación'
    )

    padece_enfermedad = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No')
    ], string='¿Padece Alguna Enfermedad?', default='no')

    enfermedades = fields.Text(
        string='Enfermedades',
        help='Especificar enfermedades'
    )

    usa_computadora = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No')
    ], string='¿Usa Computadora?', default='no')

    antecedentes_familiares = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No')
    ], string='¿Antecedentes Familiares?', default='no')

    antecedentes_familiares_detalle = fields.Text(
        string='Detalle Antecedentes Familiares',
        help='Glaucoma, cataratas, degeneración macular, etc.'
    )

    usa_lentes = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('anteriormente', 'Anteriormente')
    ], string='¿Ha Usado Lentes?', default='no')

    tipo_lentes_previos = fields.Char(
        string='Tipo de Lentes Previos',
        help='Si ha usado lentes, especificar qué tipo'
    )

    # Condiciones médicas específicas
    embarazo = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿Embarazo?', default='na')

    diabetes = fields.Boolean(string='Diabetes')
    presion_arterial = fields.Boolean(string='Presión Arterial')
    cirugia_previa = fields.Boolean(string='Cirugía Ocular Previa (CX)')

    # SÍNTOMAS
    sintoma_cefalea = fields.Boolean(string='Cefalea')
    sintoma_ardor = fields.Boolean(string='Ardor')
    sintoma_dolor = fields.Boolean(string='Dolor')
    sintoma_ojo_rojo = fields.Boolean(string='Ojo Rojo')
    sintoma_fotofobia = fields.Boolean(string='Fotofobia')
    sintoma_glaucoma = fields.Boolean(string='Glaucoma')
    sintoma_vision_borrosa = fields.Boolean(string='Visión Borrosa')
    sintoma_secreciones = fields.Boolean(string='Secreciones')
    sintoma_cansancio = fields.Boolean(string='Cansancio')
    sintoma_moscas_volantes = fields.Boolean(string='Moscas Volantes')
    sintoma_otros = fields.Boolean(string='Otros Síntomas')
    sintoma_otros_descripcion = fields.Char(string='Especificar Otros Síntomas')

    # Observaciones generales
    alergias = fields.Text(string='Alergias')
    notas_medicas = fields.Text(string='Notas Médicas Adicionales')

    # Relaciones con consultas y citas
    consulta_ids = fields.One2many(
        'optica.consulta',
        'partner_id',
        string='Consultas'
    )
    cita_optica_ids = fields.One2many(
        'optica.cita',
        'partner_id',
        string='Citas de Óptica'
    )

    # Contadores
    consulta_count = fields.Integer(
        string='Número de Consultas',
        compute='_compute_consulta_count'
    )
    cita_optica_count = fields.Integer(
        string='Número de Citas',
        compute='_compute_cita_optica_count'
    )

    # Última consulta
    ultima_consulta_id = fields.Many2one(
        'optica.consulta',
        string='Última Consulta',
        compute='_compute_ultima_consulta'
    )
    ultima_consulta_fecha = fields.Date(
        related='ultima_consulta_id.fecha',
        string='Fecha Última Consulta'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_optica_patient') and not vals.get('ficha_numero'):
                vals['ficha_numero'] = self.env['ir.sequence'].next_by_code('optica.paciente.ficha') or 'Nuevo'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('is_optica_patient'):
            for record in self:
                if not record.ficha_numero:
                    vals['ficha_numero'] = self.env['ir.sequence'].next_by_code('optica.paciente.ficha') or 'Nuevo'
        return super().write(vals)

    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        today = fields.Date.today()
        for record in self:
            if record.fecha_nacimiento:
                record.edad = relativedelta(today, record.fecha_nacimiento).years
            else:
                record.edad = 0

    @api.depends('consulta_ids')
    def _compute_consulta_count(self):
        for record in self:
            record.consulta_count = len(record.consulta_ids)

    @api.depends('cita_optica_ids')
    def _compute_cita_optica_count(self):
        for record in self:
            record.cita_optica_count = len(record.cita_optica_ids)

    @api.depends('consulta_ids', 'consulta_ids.fecha')
    def _compute_ultima_consulta(self):
        for record in self:
            if record.consulta_ids:
                record.ultima_consulta_id = record.consulta_ids.sorted('fecha', reverse=True)[0]
            else:
                record.ultima_consulta_id = False

    def action_ver_consultas(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consultas de %s' % self.name,
            'res_model': 'optica.consulta',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_ver_citas_optica(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Citas de %s' % self.name,
            'res_model': 'optica.cita',
            'view_mode': 'list,calendar,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_nueva_cita_optica(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Cita',
            'res_model': 'optica.cita',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id}
        }

    def action_nueva_consulta(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Consulta',
            'res_model': 'optica.consulta',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_partner_id': self.id}
        }
