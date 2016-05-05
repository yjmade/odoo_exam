# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Exam(models.Model):
    _name = 'examin.exam'
    _rec_name = "name"

    name = fields.Text()
    question_num = fields.Integer()
    category = fields.Many2one("examin.question.category")
    user_lines = fields.One2many("examin.user.participant", "examin")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    time_limit_hours = fields.Float()


class Question(models.Model):
    _name = "examin.question"
    _rec_name = "body"

    category = fields.Many2one("examin.question.category")
    body = fields.Text()
    choice_a = fields.Text()
    choice_b = fields.Text()
    choice_c = fields.Text()
    choice_d = fields.Text()
    answer = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ])


class Category(models.Model):
    _name = "examin.question.category"
    _rec_name = "name"

    name = fields.Text()
    questions = fields.One2many("examin.question", "category")
    exams = fields.One2many("examin.exam", "category")
    question_count = fields.Integer(compute="_get_question_count")

    @api.multi
    @api.depends("questions")
    def _get_question_count(self):
        counts = {group["category"][0]: group["category_count"] for group in self.env["examin.question"].read_group([["category.id", "in", self.ids]], [], ["category"])}
        for rec in self:
            rec.question_count = counts.get(rec.id, 0)

    @api.multi
    def action_questions(self, *args, **kwargs):
        return {
            'name': self.name,
            'view_mode': 'tree,form',
            # 'view_type': 'tree',
            'res_model': 'examin.question',
            # 'res_id': partial_id,
            'type': 'ir.actions.act_window',
            # 'nodestroy': True,
            # 'target': 'new',
            'domain': '[("category.id","=",%s)]' % self.id,
        }


class UserExamin(models.Model):
    _name = "examin.user.participant"

    user = fields.Many2one("user")
    examin = fields.Many2one("examin.exam")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    lines = fields.One2many("examin.user.participant.line", "user_examin")
    result = fields.Float()


class UserExaminLine(models.Model):
    _name = "examin.user.participant.line"

    user_examin = fields.Many2one("examin.user.participant")
    seq = fields.Integer()
    question = fields.Many2one("examin.question")
    answer = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ])
    answer_time = fields.Datetime()
