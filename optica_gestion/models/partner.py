from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Identificar como paciente de óptica
    is_optica_patient = fields.Boolean(
        string='Es Paciente de Óptica',
        default=False
    )

    # Lista negra para óptica
    blacklisted = fields.Boolean(
        string='Lista Negra',
        default=False,
        help='Marcar pacientes problemáticos'
    )
    blacklist_motivo = fields.Text(
        string='Motivo',
        help='Motivo por el cual está en lista negra'
    )

    # Número de ficha
    ficha_numero = fields.Char(
        string='Ficha No.',
        readonly=True,
        copy=False
    )

    # Dirección simple para pacientes (en lugar de street/city/zip separados)
    direccion_paciente = fields.Char(
        string='Dirección',
        help='Dirección del paciente'
    )

    # Datos adicionales del paciente (nombres coinciden con Excel)
    fecha = fields.Date(
        string='Fecha',
        default=fields.Date.today,
        help='Fecha de registro del paciente'
    )
    edad = fields.Integer(
        string='Edad'
    )
    ocupacion = fields.Char(
        string='Ocupación'
    )
    referencia = fields.Char(
        string='Referencia',
        help='¿Cómo se enteró de nosotros?'
    )

    # Preguntas de la ficha (Boolean para coincidir con Excel 0/1)
    ev_visual = fields.Boolean(
        string='Se ha realizado alguna evaluación visual'
    )
    ob_ev_visual = fields.Text(
        string='Observaciones Evaluación Visual'
    )

    enfermedad = fields.Boolean(
        string='Padece de alguna enfermedad'
    )
    ob_enfermedad = fields.Text(
        string='Observaciones Enfermedad'
    )

    computadora = fields.Boolean(
        string='Usa computadora'
    )
    ob_computadora = fields.Text(
        string='Observaciones Computadora'
    )

    lentes = fields.Boolean(
        string='Ha usado lentes'
    )
    ob_lentes = fields.Text(
        string='Observaciones Lentes'
    )

    antecedentes = fields.Boolean(
        string='Antecedentes familiares'
    )
    ob_antecedentes = fields.Text(
        string='Observaciones Antecedentes'
    )

    # SÍNTOMAS (nombres exactos del Excel)
    cefalea = fields.Boolean(string='Cefalea')
    vision_borrosa = fields.Boolean(string='Visión Borrosa')
    dolor = fields.Boolean(string='Dolor')
    ojo_rojo = fields.Boolean(string='Ojo Rojo')
    fotofobia = fields.Boolean(string='Fotofobia')
    glaucoma = fields.Boolean(string='Glaucoma')
    diabetes = fields.Boolean(string='Diabetes')
    secreciones = fields.Boolean(string='Secreciones')
    cansancio = fields.Boolean(string='Cansancio')
    volantes = fields.Boolean(string='M. Volantes')
    ardor = fields.Boolean(string='Ardor')
    embarazo = fields.Boolean(string='Embarazo')
    presion = fields.Boolean(string='Presión')
    cx = fields.Boolean(string='CX')
    otros = fields.Boolean(string='Otros')

    # Observaciones clínicas generales (del Excel)
    anexos_oculares = fields.Text(string='Anexos Oculares')
    fondo_ojo = fields.Text(string='Fondo de Ojo')
    observaciones = fields.Text(string='Observaciones')

    # Relaciones con consultas
    consulta_ids = fields.One2many(
        'optica.consulta',
        'partner_id',
        string='Consultas'
    )

    # Contadores
    consulta_count = fields.Integer(
        string='Número de Consultas',
        compute='_compute_consulta_count',
        store=True
    )

    # Última consulta
    ultima_consulta_id = fields.Many2one(
        'optica.consulta',
        string='Última Consulta',
        compute='_compute_ultima_consulta',
        store=True
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

    @api.depends('consulta_ids')
    def _compute_consulta_count(self):
        for record in self:
            record.consulta_count = len(record.consulta_ids)

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
