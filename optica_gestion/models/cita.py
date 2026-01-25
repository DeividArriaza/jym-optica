from odoo import models, fields, api
from datetime import timedelta


class OpticaCita(models.Model):
    _name = 'optica.cita'
    _description = 'Cita de Óptica'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, hora_inicio'

    partner_id = fields.Many2one(
        'res.partner',
        string='Paciente',
        required=True,
        ondelete='cascade',
        tracking=True,
        domain=[('is_optica_patient', '=', True)]
    )
    
    fecha = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    hora_inicio = fields.Float(
        string='Hora de Inicio',
        required=True,
        default=9.0
    )
    
    hora_fin = fields.Float(
        string='Hora de Fin',
        compute='_compute_hora_fin',
        store=True
    )
    
    duracion = fields.Float(
        string='Duración (horas)',
        default=0.5
    )
    
    optometrista_id = fields.Many2one(
        'res.users',
        string='Optometrista',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    motivo = fields.Text(string='Motivo de la Cita')
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió')
    ], string='Estado', default='borrador', tracking=True)
    
    notas = fields.Text(string='Notas')
    
    # Integración con calendario
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Evento de Calendario',
        ondelete='set null'
    )

    @api.depends('hora_inicio', 'duracion')
    def _compute_hora_fin(self):
        for record in self:
            record.hora_fin = record.hora_inicio + record.duracion

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_calendar_event()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ['fecha', 'hora_inicio', 'duracion', 'partner_id', 'motivo']):
            for record in self:
                record._update_calendar_event()
        return res

    def unlink(self):
        for record in self:
            if record.calendar_event_id:
                record.calendar_event_id.unlink()
        return super().unlink()

    def _create_calendar_event(self):
        self.ensure_one()
        if self.calendar_event_id:
            return
        
        start_datetime = fields.Datetime.to_datetime(self.fecha)
        hours = int(self.hora_inicio)
        minutes = int((self.hora_inicio - hours) * 60)
        start_datetime = start_datetime.replace(hour=hours, minute=minutes)
        
        duration_hours = int(self.duracion)
        duration_minutes = int((self.duracion - duration_hours) * 60)
        stop_datetime = start_datetime + timedelta(hours=duration_hours, minutes=duration_minutes)
        
        event = self.env['calendar.event'].create({
            'name': f"Cita Óptica: {self.partner_id.name}",
            'start': start_datetime,
            'stop': stop_datetime,
            'description': self.motivo or '',
            'user_id': self.optometrista_id.id if self.optometrista_id else self.env.user.id,
            'partner_ids': [(4, self.partner_id.id)],
        })
        self.calendar_event_id = event.id

    def _update_calendar_event(self):
        self.ensure_one()
        if not self.calendar_event_id:
            self._create_calendar_event()
            return
        
        start_datetime = fields.Datetime.to_datetime(self.fecha)
        hours = int(self.hora_inicio)
        minutes = int((self.hora_inicio - hours) * 60)
        start_datetime = start_datetime.replace(hour=hours, minute=minutes)
        
        duration_hours = int(self.duracion)
        duration_minutes = int((self.duracion - duration_hours) * 60)
        stop_datetime = start_datetime + timedelta(hours=duration_hours, minutes=duration_minutes)
        
        self.calendar_event_id.write({
            'name': f"Cita Óptica: {self.partner_id.name}",
            'start': start_datetime,
            'stop': stop_datetime,
            'description': self.motivo or '',
            'partner_ids': [(6, 0, [self.partner_id.id])],
        })

    def action_confirmar(self):
        self.write({'state': 'confirmada'})

    def action_completar(self):
        self.write({'state': 'completada'})

    def action_cancelar(self):
        self.write({'state': 'cancelada'})

    def action_no_asistio(self):
        self.write({'state': 'no_asistio'})

    def action_reabrir(self):
        self.write({'state': 'borrador'})

    def action_crear_consulta(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Consulta',
            'res_model': 'optica.consulta',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_partner_id': self.partner_id.id}
        }
