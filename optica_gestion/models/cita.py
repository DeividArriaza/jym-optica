from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import pytz


class OpticaCita(models.Model):
    _name = 'optica.cita'
    _description = 'Cita de Óptica'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, hora_inicio'

    # Datos de contacto (solo texto, no vinculado a paciente)
    nombre = fields.Char(
        string='Nombre',
        required=True,
        tracking=True
    )
    
    telefono = fields.Char(
        string='Teléfono',
        tracking=True
    )
    
    correo = fields.Char(
        string='Correo',
        tracking=True
    )
    
    fecha = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    # Opciones de horario cada 15 minutos (7:00 - 20:00)
    HORARIOS = [
        ('7.0', '07:00'), ('7.25', '07:15'), ('7.5', '07:30'), ('7.75', '07:45'),
        ('8.0', '08:00'), ('8.25', '08:15'), ('8.5', '08:30'), ('8.75', '08:45'),
        ('9.0', '09:00'), ('9.25', '09:15'), ('9.5', '09:30'), ('9.75', '09:45'),
        ('10.0', '10:00'), ('10.25', '10:15'), ('10.5', '10:30'), ('10.75', '10:45'),
        ('11.0', '11:00'), ('11.25', '11:15'), ('11.5', '11:30'), ('11.75', '11:45'),
        ('12.0', '12:00'), ('12.25', '12:15'), ('12.5', '12:30'), ('12.75', '12:45'),
        ('13.0', '13:00'), ('13.25', '13:15'), ('13.5', '13:30'), ('13.75', '13:45'),
        ('14.0', '14:00'), ('14.25', '14:15'), ('14.5', '14:30'), ('14.75', '14:45'),
        ('15.0', '15:00'), ('15.25', '15:15'), ('15.5', '15:30'), ('15.75', '15:45'),
        ('16.0', '16:00'), ('16.25', '16:15'), ('16.5', '16:30'), ('16.75', '16:45'),
        ('17.0', '17:00'), ('17.25', '17:15'), ('17.5', '17:30'), ('17.75', '17:45'),
        ('18.0', '18:00'), ('18.25', '18:15'), ('18.5', '18:30'), ('18.75', '18:45'),
        ('19.0', '19:00'), ('19.25', '19:15'), ('19.5', '19:30'), ('19.75', '19:45'),
        ('20.0', '20:00'),
    ]

    hora_inicio = fields.Selection(
        selection=HORARIOS,
        string='Hora de Inicio',
        required=True,
        default='9.0'
    )
    
    hora_fin = fields.Selection(
        selection=HORARIOS,
        string='Hora de Fin',
        required=True,
        default='9.5'
    )
    
    # Campos Datetime computados para el calendario
    datetime_inicio = fields.Datetime(
        string='Inicio',
        compute='_compute_datetime',
        store=True
    )
    
    datetime_fin = fields.Datetime(
        string='Fin',
        compute='_compute_datetime',
        store=True
    )
    
    duracion = fields.Char(
        string='Duración',
        compute='_compute_duracion',
        store=True
    )
    
    cantidad_personas = fields.Integer(
        string='Cantidad de Personas',
        default=1,
        help='Número de personas que vendrán a la cita'
    )
    
    optometrista_id = fields.Many2one(
        'res.users',
        string='Asignado a',
        default=lambda self: self.env.user,
        tracking=True
    )

    asignado_a = fields.Char(
        string='Asignado a (Vendedor)',
        tracking=True
    )
    
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

    def _get_user_timezone(self):
        """Obtener zona horaria del usuario o usar Guatemala por defecto"""
        user_tz = self.env.user.tz or 'America/Guatemala'
        return pytz.timezone(user_tz)

    @api.onchange('hora_inicio')
    def _onchange_hora_inicio(self):
        """Al cambiar hora de inicio, auto-poner hora fin +15 min"""
        if self.hora_inicio:
            nuevo_fin = float(self.hora_inicio) + 0.25
            nuevo_fin_str = str(nuevo_fin)
            # Verificar que el valor existe en las opciones de horario
            valores_validos = [h[0] for h in self.HORARIOS]
            if nuevo_fin_str in valores_validos:
                self.hora_fin = nuevo_fin_str

    @api.depends('fecha', 'hora_inicio', 'hora_fin')
    def _compute_datetime(self):
        for record in self:
            if record.fecha and record.hora_inicio and record.hora_fin:
                hora_inicio_float = float(record.hora_inicio)
                hora_fin_float = float(record.hora_fin)
                
                # Calcular hora y minutos de inicio
                hours_inicio = int(hora_inicio_float)
                minutes_inicio = int((hora_inicio_float - hours_inicio) * 60)
                
                # Calcular hora y minutos de fin
                hours_fin = int(hora_fin_float)
                minutes_fin = int((hora_fin_float - hours_fin) * 60)
                
                # Obtener zona horaria del usuario
                user_tz = record._get_user_timezone()
                
                # Crear datetime en zona horaria local
                fecha_dt = datetime.combine(record.fecha, datetime.min.time())
                local_inicio = user_tz.localize(fecha_dt.replace(hour=hours_inicio, minute=minutes_inicio))
                local_fin = user_tz.localize(fecha_dt.replace(hour=hours_fin, minute=minutes_fin))
                
                # Convertir a UTC para guardar en BD
                record.datetime_inicio = local_inicio.astimezone(pytz.UTC).replace(tzinfo=None)
                record.datetime_fin = local_fin.astimezone(pytz.UTC).replace(tzinfo=None)
            else:
                record.datetime_inicio = False
                record.datetime_fin = False

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion(self):
        for record in self:
            if record.hora_inicio and record.hora_fin:
                inicio = float(record.hora_inicio)
                fin = float(record.hora_fin)
                diff = fin - inicio
                if diff < 0:
                    diff = 0
                horas = int(diff)
                minutos = int((diff - horas) * 60)
                record.duracion = f"{horas}:{minutos:02d}"
            else:
                record.duracion = "0:00"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_calendar_event()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ['fecha', 'hora_inicio', 'hora_fin', 'nombre', 'notas']):
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
        if self.calendar_event_id or not self.nombre:
            return
        
        hora_inicio_float = float(self.hora_inicio) if self.hora_inicio else 9.0
        hora_fin_float = float(self.hora_fin) if self.hora_fin else 9.5
        
        start_datetime = fields.Datetime.to_datetime(self.fecha)
        hours = int(hora_inicio_float)
        minutes = int((hora_inicio_float - hours) * 60)
        start_datetime = start_datetime.replace(hour=hours, minute=minutes)
        
        end_hours = int(hora_fin_float)
        end_minutes = int((hora_fin_float - end_hours) * 60)
        stop_datetime = fields.Datetime.to_datetime(self.fecha).replace(hour=end_hours, minute=end_minutes)
        
        event = self.env['calendar.event'].create({
            'name': f"Cita Óptica: {self.nombre}",
            'start': start_datetime,
            'stop': stop_datetime,
            'description': self.notas or '',
            'user_id': self.env.user.id,
        })
        self.calendar_event_id = event.id

    def _update_calendar_event(self):
        self.ensure_one()
        if not self.calendar_event_id:
            self._create_calendar_event()
            return
        if not self.nombre:
            return
        
        hora_inicio_float = float(self.hora_inicio) if self.hora_inicio else 9.0
        hora_fin_float = float(self.hora_fin) if self.hora_fin else 9.5
        
        start_datetime = fields.Datetime.to_datetime(self.fecha)
        hours = int(hora_inicio_float)
        minutes = int((hora_inicio_float - hours) * 60)
        start_datetime = start_datetime.replace(hour=hours, minute=minutes)
        
        end_hours = int(hora_fin_float)
        end_minutes = int((hora_fin_float - end_hours) * 60)
        stop_datetime = fields.Datetime.to_datetime(self.fecha).replace(hour=end_hours, minute=end_minutes)
        
        self.calendar_event_id.write({
            'name': f"Cita Óptica: {self.nombre}",
            'start': start_datetime,
            'stop': stop_datetime,
            'description': self.notas or '',
        })

    def action_guardar_borrador(self):
        return True

    def action_confirmar(self):
        self.write({'state': 'confirmada'})

    def action_completar(self):
        self.write({'state': 'completada'})

    def action_cancelar(self):
        if self.ids:
            self.env.cr.execute(
                "UPDATE optica_cita SET state = 'cancelada' WHERE id IN %s",
                [tuple(self.ids)]
            )
            self.invalidate_recordset(['state'])
        return True

    def action_no_asistio(self):
        if self.ids:
            self.env.cr.execute(
                "UPDATE optica_cita SET state = 'no_asistio' WHERE id IN %s",
                [tuple(self.ids)]
            )
            self.invalidate_recordset(['state'])
        return True

    def action_reabrir(self):
        self.write({'state': 'borrador'})
