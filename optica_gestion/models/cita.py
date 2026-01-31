from odoo import models, fields, api
from odoo.exceptions import ValidationError
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
        required=True,
        default=9.5
    )
    
    duracion = fields.Char(
        string='Duración',
        compute='_compute_duracion',
        store=True
    )
    
    cantidad_personas = fields.Integer(
        string='Cantidad de Personas',
        default=1,
        help='Número de personas que asistirán a la cita'
    )
    
    optometrista_id = fields.Many2one(
        'res.users',
        string='Asignado a',
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

    @api.onchange('partner_id')
    def _onchange_partner_id_blacklist(self):
        """Advertir si el paciente está en lista negra"""
        if self.partner_id and self.partner_id.blacklisted:
            return {
                'warning': {
                    'title': 'Paciente en Lista Negra',
                    'message': f'{self.partner_id.name} está en la Lista Negra. No se permitirá guardar esta cita.',
                    'type': 'notification'
                }
            }

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion(self):
        for record in self:
            diff = record.hora_fin - record.hora_inicio
            if diff < 0:
                diff = 0
            horas = int(diff)
            minutos = int((diff - horas) * 60)
            record.duracion = f"{horas}:{minutos:02d}"

    @api.model_create_multi
    def create(self, vals_list):
        # Validar lista negra al crear
        for vals in vals_list:
            if vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if partner.blacklisted:
                    raise ValidationError(
                        f"No se puede agendar cita para {partner.name} porque está en la Lista Negra."
                    )
        records = super().create(vals_list)
        for record in records:
            record._create_calendar_event()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ['fecha', 'hora_inicio', 'hora_fin', 'partner_id', 'motivo']):
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
        
        end_hours = int(self.hora_fin)
        end_minutes = int((self.hora_fin - end_hours) * 60)
        stop_datetime = fields.Datetime.to_datetime(self.fecha).replace(hour=end_hours, minute=end_minutes)
        
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
        
        end_hours = int(self.hora_fin)
        end_minutes = int((self.hora_fin - end_hours) * 60)
        stop_datetime = fields.Datetime.to_datetime(self.fecha).replace(hour=end_hours, minute=end_minutes)
        
        self.calendar_event_id.write({
            'name': f"Cita Óptica: {self.partner_id.name}",
            'start': start_datetime,
            'stop': stop_datetime,
            'description': self.motivo or '',
            'partner_ids': [(6, 0, [self.partner_id.id])],
        })

    def action_guardar_borrador(self):
        """Guarda la cita en estado borrador. La validación de lista negra se ejecuta automáticamente."""
        return True

    def action_confirmar(self):
        """Confirmar cita - valida lista negra"""
        for record in self:
            if record.partner_id and record.partner_id.blacklisted:
                raise ValidationError(
                    f"No se puede confirmar cita para {record.partner_id.name} porque está en la Lista Negra."
                )
        self.write({'state': 'confirmada'})

    def action_completar(self):
        self.write({'state': 'completada'})

    def action_cancelar(self):
        """Cancelar cita - usa SQL directo para evitar validaciones"""
        if self.ids:
            self.env.cr.execute(
                "UPDATE optica_cita SET state = 'cancelada' WHERE id IN %s",
                [tuple(self.ids)]
            )
            self.invalidate_recordset(['state'])
        return True

    def action_no_asistio(self):
        """Marcar como no asistió - usa SQL directo para evitar validaciones"""
        if self.ids:
            self.env.cr.execute(
                "UPDATE optica_cita SET state = 'no_asistio' WHERE id IN %s",
                [tuple(self.ids)]
            )
            self.invalidate_recordset(['state'])
        return True

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
