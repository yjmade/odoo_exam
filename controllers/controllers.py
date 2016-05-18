# -*- coding: utf-8 -*-
from openerp import http, _


class Examin(http.Controller):

    @http.route('/examin/do_exam/<int:exam_id>/', website=True, auth="user", type="http")
    def do_exam(self, exam_id, **kwargs):
        rec = http.request.env["examin.user.participant"].browse(exam_id)
        if rec.status != "examing":
            raise http.AuthenticationError(_("Exam not start"))
        return http.request.render("examin.exam_do_exam", {"exam_line": rec})

    @http.route('/examin/results', website=True, auth="user", type="http", method="POST")
    def post_exam(self, exam_id, **kwargs):
        rec = http.request.env["examin.user.participant"].browse(int(http.request.params["exam_id"]))
        for question_line in rec.lines:
            answer = http.request.params.get("question%s" % question_line.seq)
            if answer:
                question_line.answer = answer
        rec.caculate_score()
        action_user_exam_id = http.request.env["ir.model.data"].xmlid_to_res_id("examin.action_user_exam")
        return http.request.redirect("/web/#action=%s&id=%s&view_type=form" % (action_user_exam_id, rec.id))
