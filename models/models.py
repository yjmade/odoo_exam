# -*- coding: utf-8 -*-
import random
import datetime
from openerp import models, fields, api


class ExamStatus(models.Model):
    _name = "examin.exam.status"
    _order = "sequence"

    name = fields.Char(size=20)
    sequence = fields.Integer()


class Exam(models.Model):
    _name = 'examin.exam'
    _rec_name = "name"

    name = fields.Text()
    question_num = fields.Integer(string="Question Count")
    category = fields.Many2one("examin.question.category")
    user_lines = fields.One2many("examin.user.participant", "exam")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    time_limit_hours = fields.Float()
    users = fields.Many2many("res.users", compute="_get_users", inverse="_set_users")

    def get_default_status(self):
        return self.env["examin.exam.status"].search([("name", "=", "Draft")])

    status = fields.Many2one("examin.exam.status", default=get_default_status)

    @api.one
    @api.depends("user_lines")
    def _get_users(self):
        self.users = self.env["res.users"].browse([user_line.user.id for user_line in self.user_lines])

    def _set_users(self):
        exist_user_lines = {
            user_line.user: user_line
            for user_line in self.user_lines
        }
        for user in self.users:
            if user not in exist_user_lines:
                self._generate_user_line(user)

    def _generate_user_line(self, user):
        user_line_model = self.env["examin.user.participant"]
        question_line_model = self.env["examin.user.participant.line"]
        user_line = user_line_model.create({
            "user": user.id,
            "exam": self.id,
            "status": "pending",
            "score": False
        })
        ids = list(self.category.questions.ids)
        random.shuffle(ids)
        for i, question_id in enumerate(ids[:self.question_num], 1):
            question_line_model.create({
                "user_examin": user_line.id,
                "question": question_id,
                "seq": i
            })

    @api.onchange("category")
    def onchange_category(self):
        if self.category:
            self.name = "%s Test" % self.category.name
            self.question_num = self.category.question_count
        else:
            self.name = False
            self.question_num = 0

    @api.onchange("start_time")
    def onchange_start_time(self):

        if self.start_time:
            self.end_time=fields.Datetime.to_string(fields.Datetime.from_string(self.start_time)+datetime.timedelta(hours=2))
        else:
            self.end_time=False


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
            'domain': [("category.id", "=", self.id)],
            "context": {'default_category': self.id}
        }


class UserExamin(models.Model):
    _name = "examin.user.participant"
    _rec_name = "exam"
    user = fields.Many2one("res.users")
    exam = fields.Many2one("examin.exam")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    total_minutes = fields.Integer(compute="_get_total_minutes")
    lines = fields.One2many("examin.user.participant.line", "user_examin")
    score = fields.Float()
    status = fields.Selection([
        ("pending", "pending"),
        ("examing", "examing"),
        ('finish', "finish")
    ])

    @api.one
    @api.depends("start_time", "end_time")
    def _get_total_minutes(self):
        if self.start_time and self.end_time:
            self.total_minutes = (self.end_time - self.start_time).minutes()
        else:
            self.total_minutes = False


class UserExaminLine(models.Model):
    _name = "examin.user.participant.line"
    _rec_name = "question"
    _order = "seq"
    user_examin = fields.Many2one("examin.user.participant", string="Exam")
    seq = fields.Integer()
    question = fields.Many2one("examin.question")
    answer = fields.Selection([
        ("a", "A"),
        ("b", "B"),
        ("c", "C"),
        ("d", "D"),
    ], string="Choice")
    answer_time = fields.Datetime()
    display_answer = fields.Text(string="Answer", compute="_get_display_answer")
    correct = fields.Boolean(compute="_get_display_answer")

    @api.one
    @api.depends("question", "answer")
    def _get_display_answer(self):
        if self.answer:
            self.display_answer = getattr(self.question, "choice_%s" % self.answer)
            self.correct = (self.answer == self.question.answer)
        else:
            self.display_answer = False
            self.correct = False
